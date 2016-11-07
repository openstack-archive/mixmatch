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

from os import path

from oslo_config import cfg
from oslo_log import log
from oslo_cache import core as cache

LOG = log.getLogger('root')

CONF = cfg.CONF


# Proxy
proxy_group = cfg.OptGroup(name='proxy',
                           title='Proxy Config Group')

proxy_opts = [
    cfg.IntOpt('port',
               default=5001,
               help='Web Server Port'),

    cfg.ListOpt('service_providers',
                default=[],
                help='List of service providers'),

    cfg.BoolOpt('search_by_broadcast',
                default=False,
                help='Search All Service Providers on Unknown Resource ID'),

    cfg.BoolOpt('aggregation',
                default=False,
                help='Enable Aggregation when listing resources.'),

    cfg.BoolOpt('caching',
                default=True,
                help='Enable token caching using oslo.cache'),

    cfg.IntOpt('cache_time',
               default=600,
               help='How long to store cached tokens for'),

    cfg.ListOpt('image_api_versions',
                default=['v2.3', 'v2.2', 'v2.1', 'v2.0', 'v1.1', 'v1.0'],
                help='List of supported image api versions'),

    cfg.ListOpt('volume_api_versions',
                default=['v3.0', 'v2.0', 'v1.0'],
                help='List of supported volume api versions'),
]

# Keystone
keystone_group = cfg.OptGroup(name='keystone',
                              title='Keystone Config Group')

keystone_opts = [
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


CONF.register_group(proxy_group)
CONF.register_opts(proxy_opts, proxy_group)

CONF.register_group(keystone_group)
CONF.register_opts(keystone_opts, keystone_group)

# Logging
log.register_options(CONF)

# Caching
cache.configure(CONF)

MEMOIZE_SESSION = None
session_cache_region = cache.create_region()

MEMOIZE_SESSION = cache.get_memoization_decorator(
    CONF, session_cache_region, group="proxy")


def load_config():
    """Load parameters from the proxy's config file."""
    conf_files = [f for f in ['k2k-proxy.conf',
                              'etc/k2k-proxy.conf',
                              '/etc/k2k-proxy.conf'] if path.isfile(f)]
    if conf_files is not []:
        CONF(default_config_files=conf_files)


def more_config():
    """Perform configuration that must be delayed until after import time.

    This code must be delayed until the config files have been loaded.  They
    are in a separate file so that unit tests can run them without loading
    configuration from a file.
    """
    cache.configure_cache_region(CONF, session_cache_region)

    for service_provider in CONF.proxy.service_providers:

        sp_group = cfg.OptGroup(name='sp_%s' % service_provider,
                                title=service_provider)
        sp_opts = [
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
                       help="Volume Endpoint for Service Provider")
        ]

        CONF.register_group(sp_group)
        CONF.register_opts(sp_opts, sp_group)

    log.setup(CONF, 'demo')


def get_conf_for_sp(sp_id):
    """Get the configuration opject for a specifc service provider."""
    return CONF.__getattr__('sp_%s' % sp_id)
