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

import json
import os
import operator
from six.moves.urllib import parse

from mixmatch import config

CONF = config.CONF


def construct_url(service_provider, service_type,
                  version, action, project_id=None):
    """Construct the full URL for an Openstack API call."""
    conf = config.get_conf_for_sp(service_provider)

    if service_type == 'image':
        endpoint = conf.image_endpoint

        return "%(endpoint)s/%(version)s/%(action)s" % {
            'endpoint': endpoint,
            'version': version,
            'action': os.path.join(*action)
        }
    elif service_type == 'volume':
        endpoint = conf.volume_endpoint

        return "%(endpoint)s/%(version)s/%(project)s/%(action)s" % {
            'endpoint': endpoint,
            'version': version,
            'project': project_id,
            'action': os.path.join(*action)
        }


def aggregate(responses, key, params=None, path=None, detailed=True):
    """Combine responses from several clusters into one response."""
    if params:
        limit = int(params.get('limit', 0))
        sort = params.get('sort', None)
        marker = params.get('marker', None)

        sort_key = params.get('sort_key', None)
        sort_dir = params.get('sort_dir', None)

        if sort and not sort_key:
            sort_key, sort_dir = sort.split(':')
    else:
        sort_key = None
        limit = 0
        marker = None

    resource_list = []
    for location, response in responses.items():
        resources = json.loads(response.text)
        if type(resources) == dict:
            resource_list += resources[key]

    start = 0
    last = end = len(resource_list)

    if sort_key:
        resource_list = sorted(resource_list,
                               key=operator.itemgetter(sort_key),
                               reverse=_is_reverse(sort_dir))

    if marker:
        # Find the position of the resource with marker id
        # and set the list to start at the one after that.
        for index, item in enumerate(resource_list):
            if item['id'] == marker:
                start = index + 1
                break

    if limit != 0:
        end = start + limit

    # this hack is to handle GET requests to /volumes
    # we automatically make the call to /volumes/detail
    # because we need sorting information. Here we
    # remove the extra values /volumes/detail provides
    if key == 'volumes' and not detailed:
        resource_list[start:end] = \
                _remove_details(resource_list[start:end])

    response = {key: resource_list[start:end]}

    # Inject the pagination URIs
    if start > 0:
        params.pop('marker', None)
        response['start'] = '%s?%s' % (path, parse.urlencode(params))
    if end < last:
        params['marker'] = response[key][-1]['id']
        response['next'] = '%s?%s' % (path, parse.urlencode(params))

    return json.dumps(response)


def list_api_versions(service_type, url):
    api_versions = list()

    if service_type == 'image':
        supported_versions = CONF.proxy.image_api_versions

        for version in supported_versions:
            info = dict()
            if version == supported_versions[0]:
                info.update({'status': 'CURRENT'})
            else:
                info.update({'status': 'SUPPORTED'})

            info.update({
               'id':  version,
               'links': [
                   {'href': '%s/%s/' % (url,
                                        version[:-2]),
                    'rel': 'self'}
               ]
            })
            api_versions.append(info)
        return json.dumps({'versions': api_versions})

    elif service_type == 'volume':
        supported_versions = CONF.proxy.volume_api_versions

        for version in supported_versions:
            info = dict()
            if version == supported_versions[0]:
                info.update({
                    'status': 'CURRENT',
                    'min_version': version[1:],
                    'version': version[1:]
                    })
            else:
                info.update({
                    'status': 'SUPPORTED',
                    'min_version': '',
                    'version': ''
                })

            info.update({
                'id': version,
                'updated': '2014-06-28T12:20:21Z',  # FIXME
                'links': [
                    {'href': 'http://docs.openstack.org/',
                     'type': 'text/html',
                     'rel': 'describedby'},
                    {'href': '%s/%s/' % (url,
                                         version[:-2]),
                     'rel': 'self'}
                ],
                'media-types': [
                    {'base': 'application/json',
                     'type':
                         'application/vnd.openstack.volume+json;version=%s'
                             % version[1:-2]},
                    {'base': 'application/xml',
                     'type':
                         'application/vnd.openstack.volume+xml;version=%s'
                             % version[1:-2]}
                ]
            })
            api_versions.append(info)
        return json.dumps({'versions': api_versions})

    else:
        raise ValueError


def _is_reverse(order):
    """Return True if order is asc, False if order is desc"""
    if order == 'asc':
        return False
    elif order == 'desc':
        return True
    else:
        raise ValueError


def _remove_details(volumes):
    """Delete key, value pairs if key is not in keys"""
    keys = ['id', 'links', 'name']
    for i in range(len(volumes)):
        volumes[i] = {key: volumes[i][key] for key in keys}
    return volumes
