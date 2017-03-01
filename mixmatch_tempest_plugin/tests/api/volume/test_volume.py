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

from mixmatch_tempest_plugin.tests.api.volume import base
from tempest import test
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class VolumeV3Test(base.BaseVolumeTest):

    @test.attr(type='smoke')
    @decorators.idempotent_id('44d8b55e-71c6-4bab-9fbe-fc7ea770c01a')
    def test_volume_create_show(self):
        volume_name = "mixmatch_test_volume_create_show"
        volume_creation_resp = self._create_volume_at_sp(
            sp="lavender-sp",
            name=volume_name)
        volume_id = volume_creation_resp["volume"]["id"]
        volume_info = self._get_volume_info(volume_id=volume_id)

        self.assertEqual(
            '200',
            volume_info.response['status'],
            "The volume info response's status code was not 200.")

        self.assertEqual(
            volume_name,
            volume_info['volume']['name'],
            "The retrieved volume's name was not equal to the expected name.")

        self.assertEqual(
            volume_id,
            volume_info['volume']['id'],
            "The retrieved volume's name was not equal to the name response")

    @test.attr(type='smoke')
    @decorators.idempotent_id('1d3bc4a9-b5ee-449c-bc04-2765c9077ca8')
    def test_attach_volume_from_sp(self):
        volume_name = 'mixmatch_test_attach_volume_from_sp'
        volume_creation_resp = self._create_volume_at_sp(
            sp='lavender-sp',
            name=volume_name)
        volume_id = volume_creation_resp['volume']['id']

        server_creation_resp = self.create_server(
            name="mixmatch_test_attach_volume_from_sp_server")
        server_id = server_creation_resp['id']

        self.attach_volume(server_id=server_id,
                           volume_id=volume_id)
        volume_info = self.volumes_client.show_volume(
            self.volume['id'])['volume']
        self.assertIn('attachments', volume_info)
        attachment = volume_info['attachments'][0]

        self.assertEqual('/dev/%s' %
                         CONF.compute.volume_device_name,
                         attachment['device'])
        self.assertEqual(server_creation_resp['id'], attachment['server_id'])
        self.assertEqual(self.volume['id'], attachment['id'])
        self.assertEqual(self.volume['id'], attachment['volume_id'])
