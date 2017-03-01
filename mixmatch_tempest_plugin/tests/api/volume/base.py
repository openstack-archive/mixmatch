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
from tempest import clients
from tempest.lib import auth
import json
from tempest import config
from tempest.common import credentials_factory

CONF = config.CONF


class BaseVolumeTest(tempest.test.BaseTestCase):
    """Base test case class for all Mixmatch Cinder API tests."""

    _api_version = 2
    credentials = ['primary']

    @classmethod
    def skip_checks(cls):
        super(BaseVolumeTest, cls).skip_checks()

    @classmethod
    def setup_credentials(cls):
        super(BaseVolumeTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(BaseVolumeTest, cls).setup_clients()
        cls.client = cls.os.volumes_v2_client

    @classmethod
    def resource_setup(cls):
        super(BaseVolumeTest, cls).resource_setup()

        cls.snapshots = []
        cls.volumes = []
        cls.image_ref = CONF.compute.image_ref
        cls.flavor_ref = CONF.compute.flavor_ref
        cls.build_interval = CONF.volume.build_interval
        cls.build_timeout = CONF.volume.build_timeout
        cls.special_fields = {'name_field': 'name',
                              'descrip_field': 'description'}

    @classmethod
    def resource_cleanup(cls):
        super(BaseVolumeTest, cls).resource_cleanup()

    def _create_volume_at_sp(cls, sp=None, name=None):
        request_body = {
            "volume": {
                "size": 1,
                "description": None,
                "name": name,
                "consistencygroup_id": None,
                "metadata": {}
            }
        }
        response = cls.client.post(
            url="/volumes",
            headers={"MM-SERVICE-PROVIDER": sp},
            body=json.dumps(request_body)
        )
        return response

    def _get_volume_info(cls, volume_id=None):
        return cls.client.request(
            method="GET",
            url="/volumes/{}".format(
                volume_id
            )
        )
