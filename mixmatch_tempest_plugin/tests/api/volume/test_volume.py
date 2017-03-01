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
from tempest.lib import decorators
import json


class VolumeV3Test(base.BaseVolumeTest):

    @test.attr(type='smoke')
    @decorators.idempotent_id('44d8b55e-71c6-4bab-9fbe-fc7ea770c01a')
    def test_volume_create_get_info(self):
        volume_name = "mixmatch_test_volume_create_get_info"
        volume_creation_response = self._create_volume_at_sp(
            sp="lavender-sp",
            name=volume_name
        )
        volume_id = json.loads(volume_creation_response.text)["id"]
        volume_info_response = self._get_volume_info(volume_id=volume_id)
        volume_info = json.loads(volume_info_response)
        self.assertEqual(
            200,
            volume_info_response.status_code,
            "The volume info response's status code was not 200."
        )
        self.assertEqual(
            "_create_volume_at_sp",
            volume_info['name'],
            "The retrieved volume's name was not equal to the expected name."
        )
        self.assertEqual(
            volume_creation_response['id'],
            volume_info['id'],
            "The retrieved volume's name was not equal to the name response"
        )
