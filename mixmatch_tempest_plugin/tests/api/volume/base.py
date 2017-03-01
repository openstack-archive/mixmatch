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
from mixmatch_tempest_plugin.services import mixmatch_clients
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
        cls.volumes_client = mixmatch_clients.MixmatchVolumesClient(
            cls.os.auth_provider, 'volume', None)
        cls.servers_client = cls.os.servers_client

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

    @classmethod
    def _create_volume_at_sp(cls, sp=None, name=None, size=1):
        request_body = {
            "name": name,
            "snapshot_id": None,
            "volume_type": None,
            "status": "creating",
            "multiattach": False,
            "consistencygroup_id": None,
            "attach_status": "detached",
            "user_id": None,
            "imageRef": None,
            "project_id": None,
            "size": size,
            "source_volid": None,
            "metadata": {},
            "availability_zone": None,
            "description": None,
            "source_replica": None
        }
        response = cls.volumes_client.create_volume_at_sp(volume=request_body, sp=sp)
        return response

    @classmethod
    def _get_volume_info(cls, volume_id=None):
        return cls.volumes_client.show_volume(volume_id=volume_id)

    @classmethod
    def create_server(cls, name=None, flavor='m1.tiny', image='cirros-0.3.5-x86_64-disk'):
        resp = cls.servers_client.create_server(name=name,
                                                flavorRef=flavor,
                                                imageRef=image)
        return resp

    @classmethod
    def attach_volume(cls, volume_id=None, server_id=None):
        response = cls.servers_client.attach_volume(server_id=server_id, volumeId=volume_id)
        return response
