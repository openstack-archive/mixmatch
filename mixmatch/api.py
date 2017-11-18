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
from mixmatch import session

mm_api = session.mm_api


@mm_api.route('/')
@mm_api.route('')
def hello():
    return "api v0 lives!"


def register_routes():
    session.app.register_blueprint(mm_api, url_prefix=session.FEDOPS_PATH)
