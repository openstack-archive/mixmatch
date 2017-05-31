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

from os import path

from oslo_config import cfg
from oslo_log import log

from mixmatch.config import auth
from mixmatch.config import cache
from mixmatch.config import default
from mixmatch.config import service_providers

LOG = log.getLogger('root')
CONF = cfg.CONF

MODULES = [
    default,
    cache,
    auth,
    service_providers
]


def load_from_file():
    """Load parameters from the proxy's config file."""
    conf_files = [f for f in ['mixmatch.conf',
                              'etc/mixmatch/mixmatch.conf',
                              '/etc/mixmatch/mixmatch.conf'] if path.isfile(f)]
    if conf_files is not []:
        CONF(default_config_files=conf_files)


def register_opts():
    for option_module in MODULES:
        if option_module.GROUP:
            CONF.register_group(option_module.GROUP)

        if option_module.OPTS and option_module.GROUP:
            CONF.register_opts(option_module.OPTS, option_module.GROUP)
        elif option_module.OPTS:
            CONF.register_opts(option_module.OPTS)


def pre_config():
    log.register_options(CONF)

    for option_module in MODULES:
        option_module.pre_config(CONF)

    register_opts()


def post_config():
    for option_module in MODULES:
        option_module.post_config(CONF)

    log.setup(CONF, 'demo')


def configure():
    load_from_file()
    post_config()


pre_config()
