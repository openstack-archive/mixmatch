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


class TestVolumesV3(base.BaseTest):
    def setUp(self):
        super(TestVolumesV3, self).setUp()
        # TODO(knikolla): load_auth_fixtures() should be done in the base
        # class, but may conflict with the other tests which haven't been
        # migrated to these fixtures.
        self.load_auth_fixtures()

    def _construct_url(self, auth=None, target=None, sp=None,
                       resource_type='volumes'):
        if not sp:
            url = '/volume'
        else:
            url = self.service_providers[sp]['volume_endpoint']

        if auth:
            url = '%(url)s/v3/%(project_id)s/%(resource_type)s' % {
                'url': url,
                'project_id': auth.get_project_id(),
                'resource_type': resource_type
            }
            if target:
                url = '%s/%s' % (url, target)

        return url

    def test_get_messages(self):
        fake_message_list = uuid.uuid4().hex

        self.requests_fixture.get(
            self._construct_url(self.auth,
                                resource_type='messages',
                                sp='default'),
            request_headers=self.auth.get_headers(),
            text=six.u(fake_message_list),
            headers={'CONTENT-TYPE': 'application/json'}
        )
        response = self.app.get(
            self._construct_url(self.auth, resource_type='messages'),
            headers=self.auth.get_headers()
        )
        self.assertEqual(response.data, six.b(fake_message_list))

    def test_get_message(self):
        fake_message = uuid.uuid4().hex

        self.requests_fixture.get(
            self._construct_url(self.auth,
                                fake_message,
                                resource_type='messages',
                                sp='default'),
            request_headers=self.auth.get_headers(),
            text=six.u(fake_message),
            headers={'CONTENT-TYPE': 'application/json'}
        )
        response = self.app.get(
            self._construct_url(self.auth, fake_message,
                                resource_type='messages'),
            headers=self.auth.get_headers()
        )
        self.assertEqual(response.data, six.b(fake_message))


class TestVolumesV2(base.BaseTest):
    def setUp(self):
        super(TestVolumesV2, self).setUp()
        # TODO(knikolla): load_auth_fixtures() should be done in the base
        # class, but may conflict with the other tests which haven't been
        # migrated to these fixtures.
        self.load_auth_fixtures()

    def _construct_url(self, auth=None, target=None, sp=None):
        if not sp:
            url = '/volume'
        else:
            url = self.service_providers[sp]['volume_endpoint']

        if auth:
            url = '%s/v2/%s/volumes' % (url, auth.get_project_id())
            if target:
                url = '%s/%s' % (url, target)

        return url

    def test_create_volume(self):
        volume_id = uuid.uuid4().hex
        self.requests_fixture.post(
            self._construct_url(self.auth, sp='default'),
            request_headers=self.auth.get_headers(),
            text=six.u(volume_id),
            headers={'CONTENT-TYPE': 'application/json'}
        )
        response = self.app.post(
            self._construct_url(self.auth),
            headers=self.auth.get_headers(),
            data=json.dumps({'volume': {'name': 'local'}})
        )
        self.assertEqual(six.b(volume_id), response.data)

    def test_create_volume_routing(self):
        volume_id = uuid.uuid4().hex
        self.requests_fixture.post(
            self._construct_url(self.remote_auth, sp='remote1'),
            request_headers=self.remote_auth.get_headers(),
            text=six.u(volume_id),
            headers={'CONTENT-TYPE': 'application/json'}
        )
        response = self.app.post(
            self._construct_url(self.auth),
            headers=self.auth.get_headers(),
            data=json.dumps({'volume': {'name': 'local@remote1'}})
        )
        self.assertEqual(six.b(volume_id), response.data)

    def test_get_volume_local_mapping(self):
        volume_id = uuid.uuid4().hex

        insert(ResourceMapping('volumes',
                               volume_id,
                               self.auth.get_project_id(),
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

    def test_list_volumes_aggregation_no_detail(self):
        self.config_fixture.load_raw_values(aggregation=True)

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
            '/volume/v2/%s/volumes' % self.auth.get_project_id(),
            headers=self.auth.get_headers())
        actual = json.loads(response.data.decode("ascii"))
        actual['volumes'].sort(key=lambda x: x[u'id'])
        EXPECTED = samples.single_sp['/volume/v2/id/volumes']
        EXPECTED['volumes'].sort(key=lambda x: x[u'id'])
        self.assertEqual(actual, EXPECTED)

        # Test that limit and marker are popped when they are in the URL
        response = self.app.get(
            ('/volume/v2/%s/volumes?limit=1&marker=%s' %
                (self.auth.get_project_id(), uuid.uuid4().hex)),
            headers=self.auth.get_headers())
        self.assertEqual(200, response.status_code)

    def test_list_volumes_aggregation_detail(self):
        self.config_fixture.load_raw_values(aggregation=True)

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
            '/volume/v2/%s/volumes/detail' % self.auth.get_project_id(),
            headers=self.auth.get_headers())
        actual = json.loads(response.data.decode("ascii"))
        actual['volumes'].sort(key=lambda x: x[u'id'])
        EXPECTED = samples.single_sp['/volume/v2/id/volumes/detail']
        EXPECTED['volumes'].sort(key=lambda x: x[u'id'])
        self.assertEqual(actual, EXPECTED)

    def test_list_volumes_no_aggregation(self):
        self.config_fixture.load_raw_values(aggregation=False)
        local = samples.multiple_sps['/volume/v2/id/volumes/detail'][0]

        self.requests_fixture.get(
            self._construct_url(self.auth, 'detail', sp='default'),
            text=json.dumps(local),
            status_code=200,
            request_headers=self.auth.get_headers(),
            headers={'CONTENT-TYPE': 'application/json'})
        response = self.app.get(
            self._construct_url(self.auth, 'detail'),
            headers=self.auth.get_headers())
        self.assertEqual(json.loads(response.data.decode("ascii")), local)

    def test_volume_unversioned_calls_no_action_aggregation(self):
        response = self.app.get(
            '/volume',
            headers=self.auth.get_headers())
        self.assertEqual(response.status_code, 200)
        actual = json.loads(response.data.decode("ascii"))
        self.assertEqual(len(actual['versions']), 3)

    def test_unversioned_call_no_action_no_aggregation(self):
        self.config_fixture.load_raw_values(aggregation=False)
        fake_response = uuid.uuid4().hex

        self.requests_fixture.get(self._construct_url(sp='default'),
                                  text=six.u(fake_response),
                                  headers={'CONTENT-TYPE': 'application/json'})

        response = self.app.get('/volume')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, six.b(fake_response))

    def test_volume_versioned_calls_no_action(self):
        response = self.app.get(
            '/volume/v2',
            headers=self.auth.get_headers())
        self.assertEqual(response.status_code, 400)
