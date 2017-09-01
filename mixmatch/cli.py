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

from mixmatch import config
from mixmatch import model

CONF = config.CONF


def do_db_sync():
    model.create_tables()


def register_parsers(subparsers):

    db_sync = subparsers.add_parser('db_sync',
                                    description='description',
                                    help='help')
    db_sync.set_defaults(func=do_db_sync)


def main():
    command = cfg.SubCommandOpt('command',
                                title='Command',
                                help='Mixmatch management commands.',
                                handler=register_parsers)
    CONF.register_cli_opt(command)
    config.load_from_file()

    CONF.command.func()


if __name__ == '__main__':
    main()
