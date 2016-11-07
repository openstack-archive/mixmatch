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

import uuid

import requests
import flask

from flask import abort

from mixmatch import config
from mixmatch.config import LOG, CONF
from mixmatch.session import app
from mixmatch.session import chunked_reader
from mixmatch.session import request
from mixmatch import auth
from mixmatch import model
from mixmatch import services


def stream_response(response):
    yield response.raw.read()


def is_valid_uuid(value):
    try:
        uuid.UUID(value, version=4)
        return True
    except ValueError:
        return False


class RequestHandler:
    def __init__(self, method, path, headers):
        self.method = method
        self.path = path
        self.headers = headers

        self.request_path = path.split('/')

        # workaround to fix glance requests
        # that does not contain image directory
        if self.request_path[0] in ['v1', 'v2']:
            self.request_path.insert(0, 'image')

        self.service_type = self.request_path[0]

        if len(self.request_path) == 1:
            # unversioned calls with no action
            self._forward = self._list_api_versions
            return
        elif len(self.request_path) == 2:
            # versioned calls with no action
            abort(400)

        self.version = self.request_path[1]

        self.detailed = True
        if self.service_type == 'image':
            # /image/{version}/{action}
            self.action = self.request_path[2:]
        elif self.service_type == 'volume':
            # /volume/{version}/{project_id}/{action}
            self.action = self.request_path[3:]

            # if request is to /volumes, change it
            # to /volumes/detail for aggregation
            if self.method == 'GET' \
                    and self.action[-1] == 'volumes':
                self.detailed = False
                self.action.insert(len(self.action), 'detail')
        else:
            raise ValueError

        if self.method in ['GET']:
            self.stream = True
        else:
            self.stream = False

        resource_id = None
        mapping = None
        aggregate = False

        if len(self.action) > 1 and is_valid_uuid(self.action[1]):
            resource_id = self.action[1]
            mapping = model.ResourceMapping.find(
                resource_type=self.action[0],
                resource_id=resource_id)
        else:
            if self.method == 'GET' \
                    and self.action[0] in ['images', 'volumes', 'snapshots']:
                aggregate = True

        self.local_token = headers['X-AUTH-TOKEN']
        LOG.info('Local Token: %s ' % self.local_token)

        if 'MM-SERVICE-PROVIDER' in headers and 'MM-PROJECT-ID' in headers:
            # The user wants a specific service provider, use that SP.
            self.service_provider = headers['MM-SERVICE-PROVIDER']
            self.project_id = headers['MM-PROJECT-ID']
            self._forward = self._targeted_forward
        elif aggregate:
            self._forward = self._aggregate_forward
        elif mapping:
            # Which we already know the location of, use that SP.
            self.service_provider = mapping.resource_sp
            self.project_id = mapping.tenant_id
            self._forward = self._targeted_forward
        else:
            self._forward = self._search_forward

    def _do_request_on(self, sp, project_id=None):
        if sp == 'default':
            auth_session = auth.get_local_auth(self.local_token)
        else:
            auth_session = auth.get_sp_auth(sp,
                                            self.local_token,
                                            project_id)
        headers = self._prepare_headers(self.headers)
        headers['X-AUTH-TOKEN'] = auth_session.get_token()

        url = services.construct_url(
            sp,
            self.service_type,
            self.version,
            self.action,
            project_id=auth_session.get_project_id()
        )

        LOG.info('%s: %s' % (self.method, url))

        if self.chunked:
            return requests.request(method=self.method,
                                    url=url,
                                    headers=headers,
                                    data=chunked_reader())
        else:
            return requests.request(method=self.method,
                                    url=url,
                                    headers=headers,
                                    data=request.data,
                                    stream=self.stream,
                                    params=self._prepare_args(request.args))

    def _finalize(self, response):
        if not self.stream:
            final_response = flask.Response(
                response.text,
                response.status_code
            )
            for key, value in response.headers.items():
                final_response.headers[key] = value
        else:
            final_response = flask.Response(
                flask.stream_with_context(stream_response(response)),
                response.status_code,
                content_type=response.headers['content-type']
            )
        return final_response

    def _local_forward(self):
        return self._finalize(self._do_request_on('default'))

    def _targeted_forward(self):
        return self._finalize(
            self._do_request_on(self.service_provider, self.project_id))

    def _search_forward(self):
        if not CONF.proxy.search_by_broadcast:
            return self._local_forward()

        for sp in CONF.proxy.service_providers:
            if sp == 'default':
                response = self._do_request_on('default')
                if 200 <= response.status_code < 300:
                    return self._finalize(response)
            else:
                self.service_provider = sp
                for project in auth.get_projects_at_sp(sp, self.local_token):
                    response = self._do_request_on(sp, project)
                    if 200 <= response.status_code < 300:
                        return self._finalize(response)
        return flask.Response(
            "Not found\n.",
            404
        )

    def _aggregate_forward(self):
        if not CONF.proxy.aggregation:
            return self._local_forward()

        responses = {}

        for sp in CONF.proxy.service_providers:
            if sp == 'default':
                responses['default'] = self._do_request_on('default')
            else:
                for proj in auth.get_projects_at_sp(sp, self.local_token):
                    responses[(sp, proj)] = self._do_request_on(sp, proj)

        return flask.Response(
            services.aggregate(responses,
                               self.action[0],
                               request.args.to_dict(),
                               request.base_url,
                               detailed=self.detailed),
            200,
            content_type=responses['default'].headers['content-type']
        )

    def _list_api_versions(self):
        return services.list_api_versions(self.service_type,
                                          request.base_url)

    def forward(self):
        return self._forward()

    @staticmethod
    def _prepare_headers(user_headers):
        headers = dict()
        headers['Accept'] = user_headers.get('Accept', '')
        headers['Content-Type'] = user_headers.get('Content-Type', '')
        for key, value in user_headers.items():
            if key.lower().startswith('x-') and key.lower() != 'x-auth-token':
                headers[key] = value
        return headers

    @staticmethod
    def _prepare_args(user_args):
        """Prepare the GET arguments by removing the limit and marker.

        This is because the id of the marker will only be present in one of
        the service providers.
        """
        args = user_args.copy()
        args.pop('limit', None)
        args.pop('marker', None)
        return args

    @property
    def chunked(self):
        return self.headers.get('Transfer-Encoding', '').lower() == 'chunked'


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT',
                                                'DELETE', 'HEAD', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT',
                                    'DELETE', 'HEAD', 'PATCH'])
def proxy(path):
    k2k_request = RequestHandler(request.method, path, request.headers)
    return k2k_request.forward()


def main():
    config.load_config()
    config.more_config()
    model.create_tables()


if __name__ == "__main__":
    main()
    app.run(port=5001, threaded=True)
