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

import six
import json

from mixmatch.tests.unit.base import setUp

from mixmatch.model import insert, ResourceMapping


class TestImages(setUp):
    def setUp(self):
        super(TestImages, self).setUp()

    def test_get_image(self):
        self.session_fixture.add_local_auth('wewef', 'my_project_id')
        insert(ResourceMapping("images", "6c4ae06e14bd422e97afe07223c99e18",
                               "not-to-be-read", "default"))

        EXPECTED = 'WEOFIHJREINJEFDOWEIJFWIENFERINWFKEWF'
        self.requests_fixture.get(
            'http://images.local/v2/images/'
            '6c4ae06e-14bd-422e-97af-e07223c99e18',
            request_headers={'X-AUTH-TOKEN': 'wewef'},
            text=six.u(EXPECTED),
            headers={'CONTENT-TYPE': 'application/json'})
        response = self.app.get(
            '/image/v2/images/6c4ae06e-14bd-422e-97af-e07223c99e18',
            headers={'X-AUTH-TOKEN': 'wewef',
                     'CONTENT-TYPE': 'application/json'})
        self.assertEqual(response.data, six.b(EXPECTED))

    def test_get_image_remote(self):
        REMOTE_PROJECT_ID = "319d8162b38342609f5fafe1404216b9"
        LOCAL_TOKEN = "my-local-token"
        REMOTE_TOKEN = "my-remote-token"

        self.session_fixture.add_sp_auth('remote1', LOCAL_TOKEN,
                                         REMOTE_PROJECT_ID, REMOTE_TOKEN)
        insert(ResourceMapping("images", "6c4ae06e14bd422e97afe07223c99e18",
                               REMOTE_PROJECT_ID, "remote1"))

        EXPECTED = 'WEOFIHJREINJEFDOWEIJFWIENFERINWFKEWF'
        self.requests_fixture.get(
            'http://images.remote1/v2/images/'
            '6c4ae06e-14bd-422e-97af-e07223c99e18',
            text=six.u(EXPECTED),
            request_headers={'X-AUTH-TOKEN': REMOTE_TOKEN},
            headers={'CONTENT-TYPE': 'application/json'})
        response = self.app.get(
            '/image/v2/images/6c4ae06e-14bd-422e-97af-e07223c99e18',
            headers={'X-AUTH-TOKEN': LOCAL_TOKEN,
                     'CONTENT-TYPE': 'application/json'})
        self.assertEqual(response.data, six.b(EXPECTED))

    def test_get_image_default_to_local(self):
        self.session_fixture.add_local_auth('wewef', 'my_project_id')

        self.requests_fixture.get(
            'http://images.local/v2/images/'
            '6c4ae06e-14bd-422e-97af-e07223c99e18',
            text="nope.",
            status_code=400,
            request_headers={'X-AUTH-TOKEN': 'wewef'},
            headers={'CONTENT-TYPE': 'application/json'})
        response = self.app.get(
            '/image/v2/images/6c4ae06e-14bd-422e-97af-e07223c99e18',
            headers={'X-AUTH-TOKEN': 'wewef',
                     'CONTENT-TYPE': 'application/json'})
        self.assertEqual(response.status_code, 400)

    def test_get_image_search_local(self):
        self.config_fixture.load_raw_values(search_by_broadcast=True)
        self.session_fixture.add_local_auth('wewef', 'my_project_id')

        IMAGE = 'Here is my image.'

        self.requests_fixture.get(
            'http://images.local/v2/images/'
            '6c4ae06e-14bd-422e-97af-e07223c99e18',
            text=six.u(IMAGE),
            status_code=200,
            request_headers={'X-AUTH-TOKEN': 'wewef'},
            headers={'CONTENT-TYPE': 'application/json'})
        # Don't add a response for the remote SP, to ensure that our code
        # always checks locally first.

        response = self.app.get(
            '/image/v2/images/6c4ae06e-14bd-422e-97af-e07223c99e18',
            headers={'X-AUTH-TOKEN': 'wewef',
                     'CONTENT-TYPE': 'application/json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, six.b(IMAGE))

    def test_get_image_search_remote(self):
        REMOTE_PROJECT_ID = "319d8162b38342609f5fafe1404216b9"
        self.config_fixture.load_raw_values(search_by_broadcast=True)
        self.session_fixture.add_local_auth('local-tok', 'my_project_id')
        self.session_fixture.add_sp_auth('remote1', 'local-tok',
                                         REMOTE_PROJECT_ID, 'remote-tok')
        self.session_fixture.add_project_at_sp('remote1', REMOTE_PROJECT_ID)

        IMAGE = 'Here is my image.'

        self.requests_fixture.get(
            'http://images.local/v2/images/'
            '6c4ae06e-14bd-422e-97af-e07223c99e18',
            text="nope.",
            status_code=400,
            request_headers={'X-AUTH-TOKEN': 'local-tok'},
            headers={'CONTENT-TYPE': 'application/json'})
        self.requests_fixture.get(
            'http://images.remote1/v2/images/'
            '6c4ae06e-14bd-422e-97af-e07223c99e18',
            text=six.u(IMAGE),
            status_code=200,
            request_headers={'X-AUTH-TOKEN': 'remote-tok'},
            headers={'CONTENT-TYPE': 'application/json'})

        response = self.app.get(
            '/image/v2/images/6c4ae06e-14bd-422e-97af-e07223c99e18',
            headers={'X-AUTH-TOKEN': 'local-tok',
                     'CONTENT-TYPE': 'application/json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, six.b(IMAGE))

    def test_get_image_search_nexists(self):
        REMOTE_PROJECT_ID = "319d8162b38342609f5fafe1404216b9"
        self.config_fixture.load_raw_values(search_by_broadcast=True)
        self.session_fixture.add_local_auth('local-tok', 'my_project_id')
        self.session_fixture.add_sp_auth('remote1', 'local-tok',
                                         REMOTE_PROJECT_ID, 'remote-tok')
        self.session_fixture.add_project_at_sp('remote1', REMOTE_PROJECT_ID)

        self.requests_fixture.get(
            'http://images.local/v2/images/'
            '6c4ae06e-14bd-422e-97af-e07223c99e18',
            text="nope.",
            status_code=400,
            request_headers={'X-AUTH-TOKEN': 'local-tok'},
            headers={'CONTENT-TYPE': 'application/json'})
        self.requests_fixture.get(
            'http://images.remote1/v2/images/'
            '6c4ae06e-14bd-422e-97af-e07223c99e18',
            text="also nope.",
            status_code=403,
            request_headers={'X-AUTH-TOKEN': 'remote-tok'},
            headers={'CONTENT-TYPE': 'application/json'})

        response = self.app.get(
            '/image/v2/images/6c4ae06e-14bd-422e-97af-e07223c99e18',
            headers={'X-AUTH-TOKEN': 'local-tok',
                     'CONTENT-TYPE': 'application/json'})
        self.assertEqual(response.status_code, 404)

    def test_list_images(self):
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
                {"id": "4af2929a-3c1f-4ccf-bf91-724444719c78",
                 "size": 13167626},
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
        actual['images'].sort(key=(lambda x: x[u'id']))
        self.assertEqual(actual, EXPECTED)

    def test_image_unversioned_calls_no_action(self):
        response = self.app.get(
            '/image',
            headers={'X-AUTH-TOKEN': 'local-tok',
                     'CONTENT-TYPE': 'application/json'})
        self.assertEqual(response.status_code, 200)
        actual = json.loads(response.data.decode("ascii"))
        self.assertEqual(len(actual['versions']), 6)

    def test_image_versioned_calls_no_action(self):
        response = self.app.get(
            '/image/v2',
            headers={'X-AUTH-TOKEN': 'local-tok',
                     'CONTENT-TYPE': 'application/json'})
        self.assertEqual(response.status_code, 400)
