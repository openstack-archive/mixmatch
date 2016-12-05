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


from os import listdir
import json


class Response(object):
    def __init__(self, text):
        self.text = text


path = './mixmatch/tests/unit/sample_data/'
sample_data = {}
for filename in listdir(path):
    with open(path + filename, 'r') as f:
        sample_data[filename.split('.')[0]] = json.loads(f.read())

calls = {
    'image': {
        'v1': {
            'unpaged': "http://localhost:5001/image/v1/images",
            'paged': None
        },
        'v2': {
            'unpaged': "http://localhost:5001/image/v2/images",
            'paged': ["http://localhost:5001/image/v2/images?limit=1",
                      "http://localhost:5001/image/v2/images?marker=6c7bf9bd-\
                      47f1-426c-afd6-329237411e71&limit=1"]
        }
    },

    'volume': {
        'v1': {
            'unpaged': "http://localhost:5001/volume/v1/\
            cf7406045f844b7daf59f8bc1cc87dd6/volumes",
            'paged': None
        },
        'v2': {
            'unpaged': "http://localhost:5001/volume/v2/$OS_TENANT_ID/volumes",
            'paged': ["http://localhost:5001/volume/v1/$OS_TENANT_ID/volumes?\
            limit=1",
                      "http://localhost:5001/volume/v1/$OS_TENANT_ID/volumes?\
                      limit=1&marker=0e664f1e-3b5f-447f-8a92-3712b605a93c"]
        }
    }
}


responses = {
    'image': {
        'v1': {
            'unpaged': sample_data['image_v1_unpaged'],
            'paged': None
        },
        'v2': {
            'unpaged': sample_data['image_v2_unpaged'],
            'paged': [sample_data['image_v2_paged_a'],
                      sample_data['image_v2_paged_b']]
        }
    },

    'volume': {
        'v1': {
            'unpaged': sample_data['volume_v1_unpaged'],
            'paged': None
        },
        'v2': {
            'unpaged': sample_data['volume_v2_unpaged'],
            'paged': [sample_data['volume_v2_paged_a'],
                      sample_data['volume_v2_paged_b']]
        }
    }
}

unaggregated = {
    'image': {
        'v1': {
            'unpaged': {
                'default': Response(json.dumps(
                    sample_data['image_v1_split'][0]
                )),
                'sp1': Response(json.dumps(
                    sample_data['image_v1_split'][1]
                ))
            },
            'paged': None
        },
        'v2': {
            'unpaged': {
                'default': Response(json.dumps(
                    sample_data['image_v2_split'][0]
                )),
                'sp1': Response(json.dumps(
                    sample_data['image_v2_split'][1]
                ))
            },
            'paged': None
        }
    },

    'volume': {
        'v1': {
            'unpaged': {
                'default': Response(json.dumps(
                    sample_data['volume_v1_split'][0]
                )),
                'sp1': Response(json.dumps(
                    sample_data['volume_v1_split'][1]
                ))
            },
            'paged': None
        },
        'v2': {
            'unpaged': {
                'default': Response(json.dumps(
                    sample_data['volume_v2_split'][0]
                )),
                'sp1': Response(json.dumps(
                    sample_data['volume_v2_split'][1]
                ))
            },
            'paged': None
        }
    }
}
