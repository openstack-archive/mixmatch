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

from tempest import test
from tempest import config
from mixmatch_tempest_plugin.services import mixmatch_clients
from tempest.common import compute
from tempest.lib.common.utils import data_utils
from tempest.common import waiters

CONF = config.CONF


class BaseVolumeTest(test.BaseTestCase):
    """Base test case class for all Mixmatch Cinder API tests."""

    _api_version = 2
    credentials = ['primary']

    @classmethod
    def skip_checks(cls):
        super(BaseVolumeTest, cls).skip_checks()

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
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

        cls.servers = []
        cls.volumes = []
        cls.image_ref = CONF.compute.image_ref
        cls.flavor_ref = CONF.compute.flavor_ref
        cls.build_interval = CONF.volume.build_interval
        cls.build_timeout = CONF.volume.build_timeout
        cls.special_fields = {'name_field': 'name',
                              'descrip_field': 'description'}

    @classmethod
    def resource_cleanup(cls):
        cls.clear_volumes()
        cls.clear_servers()
        super(BaseVolumeTest, cls).resource_cleanup()

    @classmethod
    def clear_volumes(cls):
        for volume in cls.volumes:
            try:
                cls.volumes_client.delete_volume(volume['volume']['id'])
            except Exception as e:
                print(e)
                pass

        for volume in cls.volumes:
            try:
                cls.volumes_client.wait_for_resource_deletion(
                    volume['volume']['id'])
            except Exception as e:
                print(e)
                pass

    @classmethod
    def clear_servers(cls):
        for server in cls.servers:
            try:
                cls.servers_client.delete_server(server['id'])
            except Exception:
                pass
        for server in cls.servers:
            try:
                waiters.wait_for_server_termination(cls.servers_client,
                                                    server['id'])
            except Exception:
                pass

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
        volume = cls.volumes_client.create_volume_at_sp(volume=request_body,
                                                        sp=sp)
        cls.volumes.append(volume)
        return volume

    @classmethod
    def _get_volume_info(cls, volume_id=None):
        return cls.volumes_client.show_volume(volume_id=volume_id)

    @classmethod
    def create_server(cls, validatable=False, volume_backed=False,
                      **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = data_utils.rand_name(cls.__name__ + "-server")
        tenant_network = cls.get_tenant_network()
        body, servers = compute.create_test_server(
            cls.os,
            validatable,
            validation_resources=cls.validation_resources,
            tenant_network=tenant_network,
            volume_backed=volume_backed,
            **kwargs)
        waiters.wait_for_server_status(cls.servers_client,
                                       body['id'],
                                       'ACTIVE')
        cls.servers.extend(servers)
        return body

    @classmethod
    def attach_volume(cls, volume_id=None, server_id=None):
        return cls.servers_client.attach_volume(server_id=server_id,
                                                volumeId=volume_id)
