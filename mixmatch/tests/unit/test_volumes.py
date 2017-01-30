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
import uuid

from mixmatch.tests.unit import base

from mixmatch.model import insert, ResourceMapping
from mixmatch.tests.unit import samples


class TestVolumesV2(base.BaseTest):
    def setUp(self):
        super(TestVolumesV2, self).setUp()

    def _construct_url(self, auth, volume_id, sp=None):
        if not sp:
            prefix = '/volume'
        else:
            prefix = self.service_providers[sp]['volume_endpoint']

        return (
            '%s/v2/%s/volumes/%s' % (prefix, auth.get_project_id(), volume_id)
        )

    def test_get_volume_local_mapping(self):
        # FIXME(knikolla): load_auth_fixtures() should be done in the base class,
        # but conflicts with the other tests which haven't been migrated to these
        # fixtures. Comment applies to all instances in this file.
        self.load_auth_fixtures()

        volume_id = uuid.uuid4().hex

        insert(ResourceMapping('volumes', volume_id,self.auth.get_project_id(),
                               'default'))

        self.requests_fixture.get(
            self._construct_url(self.auth, volume_id, sp='default'),
            request_headers=self.auth.get_headers(),
            text=six.u(volume_id),
            headers={'CONTENT-TYPE': 'application/json'}
        )
        response = self.app.get(
            self._construct_url(self.auth, volume_id),
            headers=self.auth.get_headers()
        )
        self.assertEqual(response.data, six.b(volume_id))

    def test_get_volume_remote_mapping(self):
        self.load_auth_fixtures()

        volume_id = uuid.uuid4().hex

        insert(ResourceMapping('volumes', volume_id,
                               self.remote_auth.get_project_id(), "remote1"))

        self.requests_fixture.get(
            self._construct_url(self.remote_auth, volume_id, sp='remote1'),
            text=six.u(volume_id),
            request_headers=self.remote_auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'})
        response = self.app.get(
            self._construct_url(self.remote_auth, volume_id),
            headers=self.auth.get_headers())
        self.assertEqual(response.data, six.b(volume_id))

    def test_get_volume_no_search(self):
        self.load_auth_fixtures()
        volume_id = uuid.uuid4().hex

        self.requests_fixture.get(
            self._construct_url(self.auth, volume_id, sp='default'),
            text=six.u(volume_id),
            status_code=404,
            request_headers=self.auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'})
        response = self.app.get(
            self._construct_url(self.auth, volume_id),
            headers=self.auth.get_headers())
        self.assertEqual(response.status_code, 404)

    def test_get_volume_search_local(self):
        self.load_auth_fixtures()
        self.config_fixture.load_raw_values(search_by_broadcast=True)

        volume_id = uuid.uuid4().hex

        self.requests_fixture.get(
            self._construct_url(self.auth, volume_id, sp='default'),
            text=six.u(volume_id),
            status_code=200,
            request_headers=self.auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'})
        # Don't add a response for the remote SP, to ensure that our code
        # always checks locally first.

        response = self.app.get(
            self._construct_url(self.auth, volume_id),
            headers=self.auth.get_headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, six.b(volume_id))

    def test_get_volume_search_remote(self):
        self.load_auth_fixtures()
        self.config_fixture.load_raw_values(search_by_broadcast=True)

        volume_id = uuid.uuid4().hex

        self.requests_fixture.get(
            self._construct_url(self.auth, volume_id, sp='default'),
            status_code=404,
            request_headers=self.auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'})
        self.requests_fixture.get(
            self._construct_url(self.remote_auth, volume_id, sp='remote1'),
            text=six.u(volume_id),
            status_code=200,
            request_headers=self.remote_auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'})

        response = self.app.get(
            self._construct_url(self.auth, volume_id),
            headers=self.auth.get_headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, six.b(volume_id))

    def test_get_volume_search_nexists(self):
        self.load_auth_fixtures()
        self.config_fixture.load_raw_values(search_by_broadcast=True)

        volume_id = uuid.uuid4().hex

        self.requests_fixture.get(
            self._construct_url(self.auth, volume_id, sp='default'),
            status_code=404,
            request_headers=self.auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'})
        self.requests_fixture.get(
            self._construct_url(self.remote_auth, volume_id, sp='remote1'),
            status_code=404,
            request_headers=self.remote_auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'})

        response = self.app.get(
            self._construct_url(self.auth, volume_id),
            headers=self.auth.get_headers())
        self.assertEqual(response.status_code, 404)

    def test_list_volumes(self):
        self.load_auth_fixtures()

        self.requests_fixture.get(
            self._construct_url(self.auth, 'detail', sp='default'),
            text=json.dumps(
                samples.multiple_sps['/volume/v2/id/volumes/detail'][0]
            ),
            status_code=200,
            request_headers=self.auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'})
        self.requests_fixture.get(
            self._construct_url(self.remote_auth, 'detail', sp='remote1'),
            text=json.dumps(
                samples.multiple_sps['/volume/v2/id/volumes/detail'][1]
            ),
            status_code=200,
            request_headers=self.remote_auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'})

        response = self.app.get(
            self._construct_url(self.auth, 'detail'),
            headers=self.auth.get_headers())
        actual = json.loads(response.data.decode("ascii"))
        actual['volumes'].sort(key=lambda x: x[u'id'])
        EXPECTED = samples.single_sp['/volume/v2/id/volumes']
        EXPECTED['volumes'].sort(key=lambda x: x[u'id'])
        self.assertEqual(actual, EXPECTED)

    def test_volume_unversioned_calls_no_action(self):
        response = self.app.get(
            '/volume',
            headers=self.auth.get_headers())
        self.assertEqual(response.status_code, 200)
        actual = json.loads(response.data.decode("ascii"))
        self.assertEqual(len(actual['versions']), 3)

    def test_volume_versioned_calls_no_action(self):
        response = self.app.get(
            '/volume/v2',
            headers=self.auth.get_headers())
        self.assertEqual(response.status_code, 400)
