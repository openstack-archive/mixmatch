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
import six
import uuid

from mixmatch.tests.unit import base
from mixmatch.tests.unit import samples

from mixmatch.model import insert, ResourceMapping


class TestImages(base.BaseTest):
    def setUp(self):
        super(TestImages, self).setUp()
        # TODO(ericjuma): load_auth_fixtures() should be done in the base
        # class, but may conflict with the other tests which haven't been
        # migrated to these fixtures.
        self.load_auth_fixtures()

    def _construct_url(self, image_id='', sp=None):
        if not sp:
            url = '/image'
        else:
            url = self.service_providers[sp]['image_endpoint']
        url = '%s/v2/images' % url

        if image_id:
            url = '%s/%s' % (url, image_id)

        return url

    def test_create_image(self):
        image_id = uuid.uuid4().hex
        self.requests_fixture.post(
            self._construct_url(sp='default'),
            request_headers=self.auth.get_headers(),
            text=six.u(image_id),
            headers={'CONTENT-TYPE': 'application/json'}
        )
        response = self.app.post(
            self._construct_url(),
            headers=self.auth.get_headers(),
            data=json.dumps({'name': 'local'})
        )
        self.assertEqual(six.b(image_id), response.data)

    def test_create_image_routing(self):
        image_id = uuid.uuid4().hex
        self.requests_fixture.post(
            self._construct_url(sp='remote1'),
            request_headers=self.remote_auth.get_headers(),
            text=six.u(image_id),
            headers={'CONTENT-TYPE': 'application/json'}
        )
        response = self.app.post(
            self._construct_url(),
            headers=self.auth.get_headers(),
            data=json.dumps({'name': 'local@remote1'})
        )
        self.assertEqual(six.b(image_id), response.data)

    def test_get_image_local(self):
        image_id = uuid.uuid4().hex
        image_data = uuid.uuid4().hex
        insert(ResourceMapping(
            "images", image_id, self.auth.get_project_id(), "default"
        ))

        self.requests_fixture.get(
            self._construct_url(image_id=image_id, sp='default'),
            text=six.u(image_data),
            request_headers=self.auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'}
        )
        response = self.app.get(
            self._construct_url(image_id),
            headers=self.auth.get_headers()
        )

        self.assertEqual(response.data, six.b(image_data))

    def test_get_image_remote(self):
        image_id = uuid.uuid4().hex
        image_data = uuid.uuid4().hex
        insert(ResourceMapping(
            "images", image_id, self.remote_auth.get_project_id(), "remote1"
        ))

        self.requests_fixture.get(
            self._construct_url(image_id=image_id, sp='remote1'),
            text=six.u(image_data),
            request_headers=self.remote_auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'}
        )
        response = self.app.get(
            self._construct_url(image_id),
            headers=self.auth.get_headers()
        )

        self.assertEqual(response.data, six.b(image_data))

    def test_get_image_default_to_local(self):
        image_id = uuid.uuid4().hex
        image_data = uuid.uuid4().hex

        self.requests_fixture.get(
            self._construct_url(image_id=image_id, sp='default'),
            text=six.u(image_data),
            status_code=400,
            request_headers=self.auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'}
        )
        response = self.app.get(
            self._construct_url(image_id),
            headers=self.auth.get_headers()
        )

        self.assertEqual(response.status_code, 400)

    def test_get_image_search_local(self):
        self.config_fixture.load_raw_values(search_by_broadcast=True)
        image_id = uuid.uuid4().hex
        image_data = uuid.uuid4().hex

        self.requests_fixture.get(
            self._construct_url(image_id=image_id, sp='default'),
            text=six.u(image_data),
            status_code=200,
            request_headers=self.auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'}
        )
        # Don't add a response for the remote SP, to ensure that our code
        # always checks locally first.
        response = self.app.get(
            self._construct_url(image_id),
            headers=self.auth.get_headers()
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, six.b(image_data))

    def test_get_image_search_remote(self):
        self.config_fixture.load_raw_values(search_by_broadcast=True)
        image_id = uuid.uuid4().hex
        image_data = uuid.uuid4().hex

        self.requests_fixture.get(
            self._construct_url(image_id=image_id, sp='default'),
            status_code=400,
            request_headers=self.auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'}
        )
        self.requests_fixture.get(
            self._construct_url(image_id=image_id, sp='remote1'),
            text=six.u(image_data),
            status_code=200,
            request_headers=self.remote_auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'}
        )
        response = self.app.get(
            self._construct_url(image_id),
            headers=self.auth.get_headers()
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, six.b(image_data))

    def test_get_image_search_nexists(self):
        self.config_fixture.load_raw_values(search_by_broadcast=True)
        image_id = uuid.uuid4().hex

        self.requests_fixture.get(
            self._construct_url(image_id=image_id, sp='default'),
            status_code=400,
            request_headers=self.auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'}
        )
        self.requests_fixture.get(
            self._construct_url(image_id=image_id, sp='remote1'),
            status_code=403,
            request_headers=self.remote_auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'}
        )
        response = self.app.get(
            self._construct_url(image_id),
            headers=self.auth.get_headers()
        )

        self.assertEqual(response.status_code, 500)

    def test_list_images(self):
        self.requests_fixture.get(
            self._construct_url(sp='default'),
            text=json.dumps(samples.multiple_sps['/image/v2/images'][0]),
            status_code=200,
            request_headers=self.auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'}
        )
        self.requests_fixture.get(
            self._construct_url(sp='remote1'),
            text=json.dumps(samples.multiple_sps['/image/v2/images'][1]),
            status_code=200,
            request_headers=self.remote_auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'}
        )
        response = self.app.get(
            self._construct_url(),
            headers=self.auth.get_headers()
        )

        EXPECTED = samples.single_sp['/image/v2/images']
        EXPECTED['images'].sort(key=lambda x: x['id'])
        actual = json.loads(response.data.decode("ascii"))
        actual['images'].sort(key=lambda x: x['id'])
        self.assertEqual(actual, EXPECTED)

    def test_image_unversioned_calls_no_action(self):
        response = self.app.get(
            '/image',
            headers=self.auth.get_headers()
        )
        actual = json.loads(response.data.decode("ascii"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(actual['versions']), 6)

    def test_image_versioned_calls_no_action(self):
        response = self.app.get(
            '/image/v2',
            headers=self.auth.get_headers()
        )
        self.assertEqual(response.status_code, 400)
