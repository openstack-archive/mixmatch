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
from mixmatch.utils import trim_endpoint


class TestUtils(testcase.TestCase):
    def setUp(self):
        super(TestUtils, self).setUp()

    def test_trim_image(self):
        original = 'http://moc.example.com:9292'
        expected = original
        result = trim_endpoint(original)
        self.assertEqual(expected, result)

    def test_trim_volume(self):
        original = 'http://moc.example.com/volume/v1/%s' % uuid.uuid4().hex
        expected = 'http://moc.example.com/volume'
        result = trim_endpoint(original)
        self.assertEqual(expected, result)
