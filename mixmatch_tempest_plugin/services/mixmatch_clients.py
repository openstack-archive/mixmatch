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
from tempest.lib.services.volume.v2 import volumes_client
from tempest.lib.common import rest_client


class MixmatchVolumesClient(volumes_client.VolumesClient):

    def create_volume_at_sp(self, volume=None, sp=None):
        request_body = json.dumps({'volume': volume})
        head, body = self.post('volumes',
                               request_body,
                               extra_headers={'MM-SERVICE-PROVIDER': sp})
        body = json.loads(body)
        # self.expected_success(202, head.status)
        return rest_client.ResponseBody(head, body)
