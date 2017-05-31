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

from mixmatch.config import cache

GROUP = cfg.OptGroup(name='auth', title='Keystone Config Group')

OPTS = [
    cfg.StrOpt('auth_url',
               default='http://localhost:35357/v3',
               help='Keystone AUTH URL'),

    cfg.StrOpt('username',
               default='admin',
               help='Proxy username'),

    cfg.StrOpt('user_domain_id',
               default='default',
               help='Proxy user domain id'),

    cfg.StrOpt('password',
               default='nomoresecrete',
               help='Proxy user password'),

    cfg.StrOpt('project_name',
               default='admin',
               help='Proxy project name'),

    cfg.StrOpt('project_domain_id',
               default='default',
               help='Proxy project domain id')
]

MEMOIZE = None


def pre_config(conf):
    global MEMOIZE
    MEMOIZE = cache.get_decorator(conf, 'auth')


def post_config(conf):
    pass
