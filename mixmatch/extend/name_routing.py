#   Copyright 2017 Massachusetts Open Cloud
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

from mixmatch.extend import base
from mixmatch.session import request as mm_request

from oslo_serialization import jsonutils


class NameRouting(base.Extension):

    ROUTES = [
        base.Route(service='volume', version=None,
                   action=['volumes'], method='POST'),
        base.Route(service='image', version=None,
                   action=['images'], method='POST'),
    ]

    @staticmethod
    def _is_targeted(headers):
        return 'MM-SERVICE-PROVIDER' in headers

    def handle_request(self, request):
        if self._is_targeted(request['headers']):
            return

        body = jsonutils.loads(mm_request.data)
        key = None
        if 'volume' in body:
            key = 'volume'
        elif 'image' in body:
            key = 'image'
        if key and 'name' in body[key]:
            name = body[key]['name'].split('@')
            if len(name) == 2:
                request['headers']['MM-SERVICE-PROVIDER'] = name[1]
