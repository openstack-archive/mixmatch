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
import json
import requests.models

from oslo_config import fixture as config_fixture

from mixmatch import proxy
from mixmatch.config import CONF
from mixmatch.tests.unit.base import BaseTest


class TestRequestHandler(BaseTest):

    def setUp(self):
        super(TestRequestHandler, self).setUp()
        self.config_fixture = self.useFixture(config_fixture.Config(conf=CONF))

    def test_prepare_headers(self):
        user_headers = {
            'x-auth-token': 'auth token',
            'x-service-token': 'service token',
            'X-AUTH-TOKEN': 'AUTH TOKEN',
            'X-SERVICE-TOKEN': 'SERVICE TOKEN',

            'x-tra cheese': 'extra cheese',
            'x-goth-token': 'x-auth-token',
            'X-MEN': 'X MEN',

            'y-men': 'y men',
            'extra cheese': 'x-tra cheese',
            'y-auth-token': 'x-auth-token',
            'xauth-token': 'x-auth-token',
            'start-x': 'startx',

            'OpenStack-API-Version': 'volume 3.0'
        }
        expected_headers = {
            'x-tra cheese': 'extra cheese',
            'x-goth-token': 'x-auth-token',
            'X-MEN': 'X MEN',
            'Accept': '',
            'Content-Type': '',
            'OpenStack-API-Version': 'volume 3.0'
        }
        headers = proxy.RequestHandler._prepare_headers(user_headers)
        self.assertEqual(expected_headers, headers)

    def test_strip_tokens_from_logs(self):
        token = uuid.uuid4()
        headers = {
            'x-auth-token': token,
            'X-AUTH-TOKEN': token,
            'not a token': 'not a token',
            'X-Service-Token': token,
            'x-service-token': token
        }
        stripped_headers = proxy.strip_tokens_from_headers(headers)
        self.assertFalse(token in stripped_headers.values())
        self.assertTrue('not a token' in stripped_headers.values())

    def test_prepare_args(self):
        user_args = {
            'limit': 1,
            'marker': uuid.uuid4()
        }
        args = proxy.RequestHandler._prepare_args(user_args)
        self.assertEqual({}, args)

    def test_toggle_services(self):
        self.config_fixture.load_raw_values(
            group='sp_remote1',
            enabled_services='volume'
        )
        REMOTE_PROJECT_ID = "319d8162b38342609f5fafe1404216b9"
        self.session_fixture.add_local_auth(self.auth)
        self.session_fixture.add_sp_auth('remote1', self.auth.get_token(),
                                         self.remote_auth)
        self.session_fixture.add_project_at_sp('remote1', REMOTE_PROJECT_ID)

        LOCAL_IMAGES = {
            "images": [
                {"id": "1bea47ed-f6a9-463b-b423-14b9cca9ad27",
                 "size": 4096},
                {"id": "781b3762-9469-4cec-b58d-3349e5de4e9c",
                 "size": 476704768}
            ],
        }

        self.requests_fixture.get(
            'http://images.local/v2/images',
            text=json.dumps(LOCAL_IMAGES),
            status_code=200,
            request_headers={'X-AUTH-TOKEN': self.auth.get_token()},
            headers={'CONTENT-TYPE': 'application/json'})

        response = self.app.get(
            '/image/v2/images',
            headers={'X-AUTH-TOKEN': self.auth.get_token(),
                     'CONTENT-TYPE': 'application/json'})
        actual = json.loads(response.get_data(as_text=True))
        self.assertEqual(actual, LOCAL_IMAGES)

    def test_toggle_services_no_sps(self):
        self.config_fixture.load_raw_values(
            group='sp_remote1',
            enabled_services='volume'
        )
        self.config_fixture.load_raw_values(
            group='sp_default',
            enabled_services='volume'
        )
        REMOTE_PROJECT_ID = "319d8162b38342609f5fafe1404216b9"
        self.session_fixture.add_local_auth(self.auth)
        self.session_fixture.add_sp_auth('remote1', self.auth.get_token(),
                                         self.remote_auth)
        self.session_fixture.add_project_at_sp('remote1', REMOTE_PROJECT_ID)

        response = self.app.get(
            '/image/v2/images',
            headers={'X-AUTH-TOKEN': 'local-tok',
                     'CONTENT-TYPE': 'application/json'})
        actual = json.loads(response.get_data(as_text=True))
        self.assertEqual(actual, {'images': []})

    def test_is_json_response(self):
        response = requests.models.Response()
        response.headers['Content-Type'] = 'application/json'
        self.assertTrue(proxy.is_json_response(response))
        response.headers['Content-Type'] = 'application/text'
        self.assertFalse(proxy.is_json_response(response))
