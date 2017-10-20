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

from testtools import testcase

from mixmatch.extend import base


class FakeRequest:
    def __init__(self, path, method):
        self.path = path
        self.full_path = path
        self.environ = {'REQUEST_METHOD': method}


class TestRoutes(testcase.TestCase):
    def setUp(self):
        super(TestRoutes, self).setUp()
        self.ext = base.Extension()

    def test_no_routes_matches(self):
        self.ext.ROUTES = []
        self.assertTrue(self.ext.matches(FakeRequest('service/version', 'GET')))

    def test_simple_routes(self):
        self.ext.ROUTES = [('service', [])]
        self.assertTrue(self.ext.matches(FakeRequest('service', 'GET')))
        self.assertTrue(self.ext.matches(FakeRequest('service/', 'GET')))
        self.assertFalse(self.ext.matches(FakeRequest('not-service', 'GET')))

        self.ext.ROUTES = [('service', []), ('not-service', [])]
        self.assertTrue(self.ext.matches(FakeRequest('service', 'GET')))
        self.assertTrue(self.ext.matches(FakeRequest('not-service', 'GET')))

        self.ext.ROUTES = [('service', ['GET'])]
        self.assertTrue(self.ext.matches(FakeRequest('service', 'GET')))
        self.assertFalse(self.ext.matches(FakeRequest('service', 'POST')))

        self.ext.ROUTES = [('service', ['GET', 'POST'])]
        self.assertTrue(self.ext.matches(FakeRequest('service', 'GET')))
        self.assertTrue(self.ext.matches(FakeRequest('service', 'POST')))

    def test_wildcard_routes(self):
        self.ext.ROUTES = [('service/{version}', [])]
        self.assertTrue(self.ext.matches(FakeRequest('service/v1', 'GET')))
        self.assertTrue(self.ext.matches(FakeRequest('service/v2', 'GET')))
        self.assertFalse(self.ext.matches(FakeRequest('service', 'GET')))
        self.assertFalse(self.ext.matches(FakeRequest('service/', 'GET')))

        self.ext.ROUTES = [('service/{version}/resource', [])]
        self.assertTrue(self.ext.matches(FakeRequest('service/v1/resource', 'GET')))
        self.assertFalse(self.ext.matches(FakeRequest('service/v1', 'GET')))
        self.assertFalse(self.ext.matches(FakeRequest('service/v1/', 'GET')))

        self.ext.ROUTES = [('service/{version}/resource/{resource_id}', [])]
        self.assertTrue(self.ext.matches(FakeRequest('service/v1/resource/123', 'GET')))
        self.assertFalse(self.ext.matches(FakeRequest('service/v1/resource/', 'GET')))
        self.assertFalse(self.ext.matches(FakeRequest('service/v1/resource', 'GET')))

