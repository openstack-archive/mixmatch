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

import uuid

from testtools import testcase

from mixmatch import proxy


class TestRequestHandler(testcase.TestCase):
    def setUp(self):
        super(TestRequestHandler, self).setUp()

    def test_prepare_headers(self):
        user_headers = {
            'x-auth-token': uuid.uuid4(),
        }
        headers = proxy.RequestHandler._prepare_headers(user_headers)
        self.assertEqual({'Accept': '', 'Content-Type': ''}, headers)

    def test_prepare_args(self):
        user_args = {
            'limit': 1,
            'marker': uuid.uuid4()
        }
        args = proxy.RequestHandler._prepare_args(user_args)
        self.assertEqual({}, args)
