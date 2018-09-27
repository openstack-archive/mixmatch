#   Copyright 2018 Massachusetts Open Cloud
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

from mixmatch.extend import base


class VolumeSize(base.RuleEngineHook):
    ROUTES = [
        ('/volume/v3/volumes', ['POST']),
    ]

    def apply_rule(self, request):
        rule = self._load_rule_definition(attr='volume_size')
        rule.decide(request.body['volume']['volume_size'])
        return service_provider
