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

from routes import mapper


class Extension(object):
    ROUTES = []
    OPTS = []

    def matches(self, request):
        route_map = mapper.Mapper()
        for (path, methods) in self.ROUTES:
            conditions = None if not methods else {'method': methods}

            route_map.connect(path.strip('/'),
                              action=self,
                              conditions=conditions)

        match = route_map.match(url=request.path.strip('/'),
                                environ=request.environ)
        return bool(match)

    def handle_request(self, request):
        pass

    def handle_response(self, response):
        pass


class FinalResponse(object):
    stream = False

    def __init__(self, text, code, headers):
        self.text = text
        self.code = code
        self.headers = headers
