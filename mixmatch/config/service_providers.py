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

OPTS = []

SP_OPTS = [
    cfg.StrOpt('sp_name',
               default="default",
               help='SP ID in Keystone Catalog. Omit for local.'),

    cfg.StrOpt('messagebus',
               help='URI to connect to message bus'),

    cfg.StrOpt('services',
               default=None,
               help='Enabled services for this service provider.'),

    cfg.StrOpt('auth_url',
               default=None,
               help='Keystone AUTH URL for Service Provider'),

    cfg.StrOpt('image_endpoint',
               default=None,
               help="Image Endpoint for Service Provider"),

    cfg.StrOpt('volume_endpoint',
               default=None,
               help="Volume Endpoint for Service Provider"),

    cfg.StrOpt('network_endpoint',
               default=None,
               help='Network Endpoint for Service Provider'),

    cfg.ListOpt('enabled_services',
                default=['image', 'volume'],
                help="Services to enable for Service Provider")
]


def pre_config(conf):
    pass


def post_config(conf):
    for service_provider in conf.service_providers:
        sp_group = cfg.OptGroup(name='sp_%s' % service_provider,
                                title=service_provider)
        conf.register_opts(SP_OPTS, sp_group)


def get(conf, sp_id):
    """Get the configuration opject for a specifc service provider."""
    return conf.__getattr__('sp_%s' % sp_id)
