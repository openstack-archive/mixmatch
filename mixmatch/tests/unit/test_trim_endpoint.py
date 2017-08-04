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
#   under the License

import uuid

from mixmatch.tests.unit import base
from  mixmatch.auth import trim_endpoint


class TrimEndpoint(base.BaseTest):
    def setUp(self):
        super(TrimEndpoint, self).setUp()
        # TODO(Ltomatsu): load_auth_fixtures() should be done in the base
        # class, but may conflict with the other tests which haven't been
        # migrated to these fixtures.
        self.load_auth_fixtures()

    def _construct_url(self, ip_address, service, version,
                       project_id=None):
        url = '%s/%s/%s' % (ip_address, service, version)
        if project_id:
            url = '%s/%s' % (url, project_id)

        return url

    def test_trim_volumev1(self):
        ip_address = 'http://jiji'
        service = 'volume'
        version = 'v1'
        project_id = uuid.uuid4().hex

        sample_url = self._construct_url(ip_address, service,
                                         version, project_id)
        test_url = trim_endpoint(sample_url)
        actual_url = self._construct_url(ip_address, service,
                                         version)

        self.assertEqual(test_url, actual_url)


    def test_trim_volumev2(self):
        ip_address = 'http://kiki'
        service = 'volume'
        version = 'v2'
        project_id = uuid.uuid4().hex

        sample_url = self._construct_url(ip_address, service,
                                         version, project_id)
        test_url = trim_endpoint(sample_url)
        actual_url = self._construct_url(ip_address, service,
                                         version)

        self.assertEqual(test_url, actual_url)


    def test_trim_volumev3(self):
        ip_address = 'http://tombo'
        service = 'volume'
        version = 'v2'
        project_id = uuid.uuid4().hex

        sample_url = self._construct_url(ip_address, service,
                                         version, project_id)
        test_url = trim_endpoint(sample_url)
        actual_url = self._construct_url(ip_address, service,
                                         version)

        self.assertEqual(test_url, actual_url)

    def test_trim_image(self):
        ip_address = 'http://ursula'
        service = 'image'
        version = 'v2'
        project_id = None

        sample_url = self._construct_url(ip_address, service,
                                         version, project_id)
        test_url = trim_endpoint(sample_url)
        actual_url = self._construct_url(ip_address, service,
                                         version)

        self.assertEqual(test_url, actual_url)

    def test_network(self):
        ip_address = 'http://osono'
        service = 'network'
        version = 'v2'
        project_id = None

        sample_url = self._construct_url(ip_address, service,
                                         version, project_id)
        test_url = trim_endpoint(sample_url)
        actual_url = self._construct_url(ip_address, service,
                                         version)

        self.assertEqual(test_url, actual_url)
