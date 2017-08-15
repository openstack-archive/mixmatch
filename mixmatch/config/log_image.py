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

from oslo_log import log
from oslo_config import cfg

LOG_image = log.getLogger('image')

GROUP = cfg.OptGroup(name='Logger_image',
                     title='Logger_image Config Group')

OPTS = [
    cfg.StrOpt('log_dir',
               default=None,
               help='The base directory used for relative log file paths.'),

    cfg.StrOpt('log_file',
               default=None,
               help='Name of log file to send logging output to.'),

    cfg.StrOpt('debug',
               default=None,
               help=('If set to true, the logging level will be '
                     'set to DEBUG instead of the default INFO level.'))
]


def pre_config(CONF):
    log.register_options(CONF)


def post_config(CONF):
    log.setup(CONF, 'image')
