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
from oslo_cache import core

GROUP = None

OPTS = [
    cfg.BoolOpt('caching',
                default=True,
                help='Enable caching.'),

    cfg.IntOpt('cache_time',
               default=600,
               help='How long to cache things.'),
]

_REGIONS = {}


def pre_config(conf):
    core.configure(conf)


def post_config(conf):
    for _, region in _REGIONS.items():
        core.configure_cache_region(conf, region)


def register_region(name):
    _REGIONS[name] = core.create_region()


def get_decorator(conf, name, group):
    return core.get_memoization_decorator(conf,
                                          _REGIONS[name],
                                          group=group)
