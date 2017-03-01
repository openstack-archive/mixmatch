# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import tempest.test
from tempest.lib.services.volume.v3 import base_client
import json


class BaseMixmatchTest(tempest.test.BaseTestCase):
    """Base test class for all mixmatch Tempest tests."""

    @classmethod
    def setup_clients(cls):
        cls.client = base_client.BaseClient()

    def _create_volume_at_sp(self, sp=None, name=None):

        request_body = {
            "volume": {
                "size": 1,
                "description": None,
                "name": name,
                "consistencygroup_id": None,
                "metadata": {}
            }
        }

        response = self.client.request(
            method="POST",
            url="http://localhost:5001/volume/v3/{}/volumes".format(
                self.client.tenant_id
            ),
            headers="MM-SERVICE-PROVIDER: {}".format(sp),
            body=json.dumps(request_body)
        )
        return response

    def _get_volume_info(self, volume_id=None):
        return self.client.request(
            method="GET",
            url="http://localhost:5001/volume/v3/{}/volumes/{}".format(
                self.client.tenant_id,
                volume_id
            )
        )
