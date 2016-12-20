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
import os


filenames = [
    'volume_list_v1',
    'volume_list_v2',
    'volume_list_paginated_v2',
    'volume_list_detail_v1',
    'volume_list_detail_v2',
    'split_volume_list_detail_v2',
    'image_list_v1',
    'image_list_v2',
    'split_image_list_v2',
    'image_list_paginated_v2',
]

data_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'sample_data', '%s.json'
)
sample_data = {s: json.loads(open(data_path % s).read()) for s in filenames}

multiple_sps = {
    '/image/v2/images': sample_data['split_image_list_v2'],
    '/volume/v2/id/volumes/detail': sample_data['split_volume_list_detail_v2']
}

single_sp = {
    '/image/v1/images': sample_data['image_list_v1'],
    '/image/v2/images': sample_data['image_list_v2'],
    '/image/v2/images?limit=1': sample_data['image_list_paginated_v2'],
    '/volume/v1/id/volumes': sample_data['volume_list_v1'],
    '/volume/v1/id/volumes/detail': sample_data['volume_list_detail_v1'],
    '/volume/v2/id/volumes': sample_data['volume_list_v2'],
    '/volume/v2/id/volumes/detail': sample_data['volume_list_detail_v2'],
    '/volume/v2/id/volumes?limit=1': sample_data['volume_list_paginated_v2']
}
