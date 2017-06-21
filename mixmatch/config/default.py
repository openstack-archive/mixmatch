#   Copyright 2017 Massachusetts Open Cloud
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

from oslo_config import cfg

GROUP = None

OPTS = [
    cfg.ListOpt('service_providers',
                default=[],
                help='List of service providers'),

    cfg.BoolOpt('search_by_broadcast',
                default=False,
                help='Search All Service Providers on Unknown Resource ID'),

    cfg.BoolOpt('aggregation',
                default=False,
                help='Enable Aggregation when listing resources.'),

    cfg.ListOpt('image_api_versions',
                default=['v2.3', 'v2.2', 'v2.1', 'v2.0', 'v1.1', 'v1.0'],
                help='List of supported image api versions'),

    cfg.ListOpt('volume_api_versions',
                default=['v3.0', 'v2.0', 'v1.0'],
                help='List of supported volume api versions'),
]


def pre_config(conf):
    pass


def post_config(conf):
    pass
