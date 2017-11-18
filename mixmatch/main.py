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
from oslo_service import wsgi as oslo_wsgi

from mixmatch import proxy
from mixmatch import api
from mixmatch import config
from mixmatch import extend

CONF = config.CONF

mmapp = None


def main():
    config.configure()
    extend.load_extensions()
    proxy.register_routes()
    api.register_routes()
    app_loader = oslo_wsgi.Loader(CONF)
    global mmapp
    mmapp = app_loader.load_app("mixmatch")


if __name__ == "__main__":
    main()
    mmapp.run(port=5001, threaded=True)
