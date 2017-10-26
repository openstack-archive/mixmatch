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
from testtools import testcase
from mixmatch.extend.base import Route


class TestRoutes(testcase.TestCase):
    def setUp(self):
        super(TestRoutes, self).setUp()

    def test_match_action_True(self):
        testRouteT = Route(None, None, None, [123, 'test'])
        self.assertEqual(testRouteT._match_action([123, 'test']), True)

    def test_match_action_False(self):
        testRouteF = Route(None, None, None, [123, 'test'])
        self.assertEqual(testRouteF._match_action([12, 'test']), False)

    def test_match_action_Different_Length(self):
        routeLen3 = Route(None, None, None, [123, 'test', None])
        routeLen2 = Route(None, None, None, [123, 'test'])
        self.assertEqual(routeLen3._match_action([123, 'test']), False)
        self.assertEqual(routeLen2._match_action([123, 'test', None]), False)

    def test_match_action_None(self):
        routeNone = Route(None, None, None, None)
        testRoute = Route(None, None, None, [123])
        self.assertEqual(routeNone._match_action([123]), True)
        self.assertEqual(testRoute._match_action(None), False)
        self.assertEqual(routeNone._match_action(None), True)
