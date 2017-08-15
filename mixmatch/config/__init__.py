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
from oslo_log import _options

from mixmatch.config import auth
from mixmatch.config import cache
from mixmatch.config import default
from mixmatch.config import service_providers

LOG = log.getLogger('root')
CONF = cfg.CONF

# Note(knikolla): Configuration modules are registered in the list below.
# Order matters, and they are loaded in the defined order.
#
# Each module must define the following variables and functions.
# * GROUP - oslo_config.cfg.OptGroup or None
# * OPTS - list of oslo_config.cfg.{Int,Str,Bool,etc}Opt or []
# * pre_config() - function is executed at module import time before OPTS
#   are registered.
# * post_config() - function is executed after the configuration files have
#   been loaded.
MODULES = [
    default,
    cache,
    auth,
    service_providers
]


def load_from_file():
    """Load options from the configuration file."""
    conf_files = [f for f in ['mixmatch.conf',
                              'etc/mixmatch/mixmatch.conf',
                              '/etc/mixmatch/mixmatch.conf'] if path.isfile(f)]
    if conf_files is not []:
        CONF(default_config_files=conf_files)


def register_opts():
    for option_module in MODULES:
        if option_module.GROUP:
            CONF.register_group(option_module.GROUP)

        if option_module.OPTS:
            CONF.register_opts(option_module.OPTS, option_module.GROUP)


def list_opts():
    return [(m.GROUP, m.OPTS) for m in MODULES]


def pre_config():
    log.register_options(CONF)

    for option_module in MODULES:
        option_module.pre_config(CONF)

    register_opts()


def post_config():
    for option_module in MODULES:
        option_module.post_config(CONF)

    log.setup(CONF, 'demo')


def set_log_file(service_name):
    cfg.set_defaults(_options.logging_cli_opts, log_file='%s.log' % (service_name))


def configure(service=None):
    if service:
        set_log_file(service)
    else:
        load_from_file()
    post_config()


pre_config()
