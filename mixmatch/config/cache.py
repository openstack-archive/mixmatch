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
                help='Enable token caching using oslo.cache'),

    cfg.IntOpt('cache_time',
               default=600,
               help='How long to store cached tokens for'),
]


def pre_config(conf):
    global _SESSION_CACHE_REGION
    core.configure(conf)
    _SESSION_CACHE_REGION = core.create_region()


def post_config(conf):
    core.configure_cache_region(conf, _SESSION_CACHE_REGION)


def get_decorator(conf, group):
    return core.get_memoization_decorator(conf,
                                          _SESSION_CACHE_REGION,
                                          group=group)
