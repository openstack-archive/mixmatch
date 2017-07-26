#   Copyright 2016 Massachusetts Open Cloud
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import collections
import six
import requests
from urllib3.util import retry
import flask
from flask import abort

from mixmatch import config
from mixmatch.config import LOG, CONF, service_providers
from mixmatch.session import app
from mixmatch.session import chunked_reader
from mixmatch.session import request
from mixmatch import auth
from mixmatch import extend
from mixmatch import model
from mixmatch import services
from mixmatch import utils

METHODS_ACCEPTED = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'PATCH']
RESOURCES_AGGREGATE = ['images', 'volumes', 'snapshots']


def stream_response(response):
    yield response.raw.read()


def get_service(a):
    """Determine service type based on path."""
    # NOTE(knikolla): Workaround to fix glance requests that do not
    # contain image as the first part of the path.
    if a[0] in ['v1', 'v2']:
        return 'image'
    else:
        service = a.pop(0)
        if service in ['image', 'volume']:
            return service
        else:
            abort(404)


def get_details(method, orig_path, headers):
    """Get details for a request."""
    path = orig_path.split('/')
    # NOTE(knikolla): Request usually look like:
    # /<service>/<version>/<project_id:uuid>/<res_type>/<res_id:uuid>
    # or
    # /<service>/<version>/<res_type>/<specific action>
    return {'method': method,
            'service': get_service(path),
            'version': utils.safe_pop(path),
            'project_id': utils.pop_if_uuid(path),
            'action': path[:],  # NOTE(knikolla): This includes
            'resource_type': utils.safe_pop(path),  # this
            'resource_id': utils.pop_if_uuid(path),  # and this
            'token': headers.get('X-AUTH-TOKEN', None),
            'headers': dict(headers),
            'path': orig_path}


def is_token_header_key(string):
    return string.lower() in ['x-auth-token', 'x-service-token']


def strip_tokens_from_headers(headers):
    return {k: '<token omitted>' if is_token_header_key(k)
            else headers[k] for k in headers}


def format_for_log(title=None, method=None, url=None, headers=None,
                   status_code=None):
    return ''.join([
        '{}:\n'.format(title) if title else '',
        'Method: {}\n'.format(method) if method else '',
        'URL: {}\n'.format(url) if url else '',
        'Headers: {}\n'.format(
            strip_tokens_from_headers(headers)) if headers else '',
        'Status Code: {}\n'.format(status_code) if status_code else ''
    ])


class RequestHandler(object):

    def __init__(self, method, path, headers):
        self.details = get_details(method, path, headers)
        self.extensions = extend.get_matched_extensions(self.details)
        self._set_strip_details(self.details)
        self.enabled_sps = filter(
            lambda sp: (self.details['service'] in
                        service_providers.get(CONF, sp).enabled_services),
            CONF.service_providers
        )

        for extension in self.extensions:
            extension.handle_request(self.details)

        if not self.details['version']:
            if CONF.aggregation:
                # unversioned calls with no action
                self._forward = self._list_api_versions
            else:
                self._forward = self._local_forward
            return

        if not self.details['resource_type']:
            # versioned calls with no action
            abort(400)

        mapping = None

        if self.details['resource_id']:
            mapping = model.ResourceMapping.find(
                resource_type=self.details['action'][0],
                resource_id=self.details['resource_id'])

        LOG.debug('Local Token: %s ' % self.details['token'])

        if 'MM-SERVICE-PROVIDER' in self.details['headers']:
            # The user wants a specific service provider, use that SP.
            # FIXME(knikolla): This isn't exercised by any unit test
            (self.service_provider, self.project_id) = (
                self.details['headers']['MM-SERVICE-PROVIDER'],
                self.details['headers'].get('MM-PROJECT-ID', None)
            )
            if self.service_provider not in self.enabled_sps:
                abort(400)
            if not self.project_id and self.service_provider != 'default':
                self.project_id = auth.get_projects_at_sp(
                    self.service_provider,
                    self.details['token']
                )[0]
            self._forward = self._targeted_forward
        elif mapping:
            # Which we already know the location of, use that SP.
            self.service_provider = mapping.resource_sp
            self.project_id = mapping.project_id
            self._forward = self._targeted_forward
        else:
            self._forward = self._forward

        LOG.info(format_for_log(title="Request to proxy",
                                method=self.details['method'],
                                url=self.details['path'],
                                headers=dict(self.details['headers'])))

    def _do_request_on(self, sp, project_id=None):
        headers = self._prepare_headers(self.details['headers'])

        if self.details['token']:
            if sp == 'default':
                auth_session = auth.get_local_auth(self.details['token'])
            else:
                auth_session = auth.get_sp_auth(sp,
                                                self.details['token'],
                                                project_id)
            headers['X-AUTH-TOKEN'] = auth_session.get_token()
            project_id = auth_session.get_project_id()
        else:
            project_id = None

        url = services.construct_url(
            sp,
            self.details['service'],
            self.details['version'],
            self.details['action'],
            project_id=project_id
        )

        request_kwargs = {
            'method': self.details['method'],
            'url': url,
            'headers': headers,
            'params': self._prepare_args(request.args)
        }
        if self.chunked:
            resp = self.session.request(data=chunked_reader(),
                                        **request_kwargs)
        else:
            resp = self.session.request(data=request.data,
                                        stream=self.stream,
                                        **request_kwargs)
        LOG.info(format_for_log(title='Request from proxy',
                                method=self.details['method'],
                                url=url,
                                headers=headers))
        LOG.info(format_for_log(title='Response to proxy',
                                status_code=resp.status_code,
                                headers=resp.headers))
        return resp

    def _finalize(self, response):
        if self.stream:
            text = flask.stream_with_context(
                stream_response(response))
        else:
            text = response.text

        final_response = flask.Response(
            text,
            response.status_code,
            headers=self._prepare_headers(response.headers)
        )
        LOG.info(format_for_log(title='Response from proxy',
                                status_code=final_response.status_code,
                                headers=dict(final_response.headers)))
        return final_response

    def _local_forward(self):
        return self._finalize(self._do_request_on('default'))

    def _targeted_forward(self):
        return self._finalize(
            self._do_request_on(self.service_provider, self.project_id))

    def _forward(self):
        if self.fallback_to_local:
            return self._local_forward()

        responses = {}
        errors = collections.defaultdict(lambda: [])

        for sp in self.enabled_sps:
            if sp == 'default':
                r = self._do_request_on('default')
                if 200 <= r.status_code < 300:
                    responses['default'] = r
                    if not self.aggregate:
                        return self._finalize(r)
                else:
                    errors[r.status_code].append(r)
            else:
                for p in auth.get_projects_at_sp(sp, self.details['token']):
                    r = self._do_request_on(sp, p)
                    if 200 <= r.status_code < 300:
                        responses[(sp, p)] = r
                        if not self.aggregate:
                            return self._finalize(r)
                    else:
                        errors[r.status_code].append(r)

        # NOTE(knikolla): If we haven't returned yet, either we're aggregating
        # or there are errors.
        if not errors:
            # TODO(knikolla): Plug this into _finalize to have a common path
            # for everything that is returned.
            return flask.Response(
                services.aggregate(responses,
                                   self.details['action'][0],
                                   self.details['service'],
                                   version=self.details['version'],
                                   params=request.args.to_dict(),
                                   path=request.base_url,
                                   strip_details=self.strip_details),
                200,
                content_type='application/json'
            )

        if six.viewkeys(errors) == {404}:
            return self._finalize(errors[404][0])
        else:
            utils.safe_pop(errors, 404)

        if len(errors.keys()) == 1:
            return self._finalize(list(errors.values())[0][0])

        # TODO(jfreud): log
        return flask.Response("Something strange happened.\n", 500)

    def _list_api_versions(self):
        return services.list_api_versions(self.details['service'],
                                          request.base_url)

    def forward(self):
        return self._forward()

    @staticmethod
    def _prepare_headers(user_headers):
        headers = dict()
        headers['Accept'] = user_headers.get('Accept', '')
        headers['Content-Type'] = user_headers.get('Content-Type', '')
        accepted_headers = ['openstack-api-version']
        for key, value in user_headers.items():
            k = key.lower()
            if ((k.startswith('x-') and not is_token_header_key(key)) or
                    k in accepted_headers):
                headers[key] = value
        return headers

    @staticmethod
    def _prepare_args(user_args):
        """Prepare the GET arguments by removing the limit and marker.

        This is because the id of the marker will only be present in one of
        the service providers.
        """
        args = user_args.copy()
        if CONF.aggregation:
            args.pop('limit', None)
            args.pop('marker', None)
        return args

    @utils.CachedProperty
    def chunked(self):
        encoding = self.details['headers'].get('Transfer-Encoding', '')
        return encoding.lower() == 'chunked'

    @utils.CachedProperty
    def stream(self):
        json = response.headers.get('Content-Type') == 'application/json'
        return (self.details['method'] == 'GET') and not json

    @utils.CachedProperty
    def fallback_to_local(self):
        """Return true if can't aggregate or search."""
        return ((self.aggregate and not CONF.aggregation) or
                (not self.aggregate and not CONF.search_by_broadcast))

    @utils.CachedProperty
    def aggregate(self):
        """Return true if this is a case where we should aggregate."""
        return (not self.details['resource_id'] and
                self.details['method'] == 'GET' and
                self.details['action'][0] in RESOURCES_AGGREGATE)

    @utils.CachedProperty
    def session(self):
        requests_session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            max_retries=retry.Retry(total=3,
                                    read=3,
                                    connect=3,
                                    backoff_factor=0.3,
                                    status_forcelist=[500, 502, 504])
        )
        requests_session.mount('http://', adapter=adapter)
        requests_session.mount('https://', adapter=adapter)
        return requests_session

    def _set_strip_details(self, details):
        # if request is to /volumes, change it
        # to /volumes/detail for aggregation
        # and set strip_details to true
        if (details['service'] == 'volume' and
                details['method'] == 'GET' and
                utils.safe_get(details['action'], -1) == 'volumes'):
            self.strip_details = True
            details['action'].insert(len(details['action']), 'detail')
        else:
            self.strip_details = False


@app.route('/', defaults={'path': ''}, methods=METHODS_ACCEPTED)
@app.route('/<path:path>', methods=METHODS_ACCEPTED)
def proxy(path):
    k2k_request = RequestHandler(request.method, path, request.headers)
    return k2k_request.forward()


def main():
    config.configure()
    model.create_tables()
    extend.load_extensions()


if __name__ == "__main__":
    main()
    app.run(port=5001, threaded=True)
