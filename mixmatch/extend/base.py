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


class Extension(object):
    ROUTES = []
    OPTS = []

    def matches(self, request):
        for route in self.ROUTES:
            if route.match(request):
                return True
        return False

    def handle_request(self, request):
        pass

    def handle_response(self, response):
        pass


class Route(object):
    def __init__(self, service=None, version=None, method=None, action=None):
        self.service = service
        self.version = version
        self.method = method
        self.action = action

    def _match_service(self, service):
        if self.service:
            return self.service == service
        return True

    def _match_version(self, version):
        if self.version:
            return self.version == version
        return True

    def _match_method(self, method):
        if self.method:
            return self.method == method
        return True

    def _match_action(self, action):
        if self.action is None:
            return True
        elif action is None:
            return False
        elif len(self.action) != len(action):
            return False
        else:
            for i in range(len(self.action)):
                if self.action[i] != action[i]:
                    return False
            return True

    def match(self, request):
        return (self._match_service(request['service']) and
                self._match_version(request['version']) and
                self._match_method(request['method']) and
                self._match_action(request['action']))
