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
from mixmatch import proxy
from mixmatch.config import CONF
from mixmatch.tests.unit.base import BaseTest
import json
from oslo_config import fixture as config_fixture


class TestRequestHandler(BaseTest):
    def setUp(self):
        super(TestRequestHandler, self).setUp()
        self.config_fixture = self.useFixture(config_fixture.Config(conf=CONF))

    def test_prepare_headers(self):
        user_headers = {
            'x-auth-token': uuid.uuid4(),
        }
        headers = proxy.RequestHandler._prepare_headers(user_headers)
        self.assertEqual({'Accept': '', 'Content-Type': ''}, headers)

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
        self.session_fixture.add_local_auth('local-tok', 'my_project_id')
        self.session_fixture.add_sp_auth('remote1', 'local-tok',
                                         REMOTE_PROJECT_ID, 'remote-tok')
        self.session_fixture.add_project_at_sp('remote1', REMOTE_PROJECT_ID)

        LOCAL_IMAGES = json.dumps({
            "images": [
                {"id": "1bea47ed-f6a9-463b-b423-14b9cca9ad27",
                 "size": 4096},
                {"id": "781b3762-9469-4cec-b58d-3349e5de4e9c",
                 "size": 476704768}
            ],
        })

        REMOTE1_IMAGES = json.dumps({
            "images": [
                {"id": "4af2929a-3c1f-4ccf-bf91-724444719c78",
                 "size": 13167626}
            ],
        })

        EXPECTED = {
            "images": [
                {"id": "1bea47ed-f6a9-463b-b423-14b9cca9ad27",
                 "size": 4096},
                {"id": "781b3762-9469-4cec-b58d-3349e5de4e9c",
                 "size": 476704768}
            ],
        }

        self.requests_fixture.get(
            'http://images.local/v2/images',
            text=LOCAL_IMAGES,
            status_code=200,
            request_headers={'X-AUTH-TOKEN': 'local-tok'},
            headers={'CONTENT-TYPE': 'application/json'})

        self.requests_fixture.get(
            'http://images.remote1/v2/images',
            text=REMOTE1_IMAGES,
            status_code=200,
            request_headers={'X-AUTH-TOKEN': 'remote-tok'},
            headers={'CONTENT-TYPE': 'application/json'})

        response = self.app.get(
            '/image/v2/images',
            headers={'X-AUTH-TOKEN': 'local-tok',
                     'CONTENT-TYPE': 'application/json'})
        actual = json.loads(response.data.decode("ascii"))
        self.assertEqual(actual, EXPECTED)
