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

from mixmatch import config

from stevedore import extension

CONF = config.CONF
LOG = config.LOG

EXTENSION_MANAGER = None  # type: extension.ExtensionManager


def load_extensions():
    global EXTENSION_MANAGER

    EXTENSION_MANAGER = extension.ExtensionManager(
        namespace='mixmatch.extend',
        invoke_on_load=True
    )


def get_matched_extensions(request):
    """Return list of matched extensions for request

    :type request: Dict[]
    :rtype: List[mixmatch.extend.base.Extension]
    """
    def _match(e):
        return e.obj if e.obj.matches(request) else None

    result = EXTENSION_MANAGER.map(_match)
    return [ext for ext in result if ext]
