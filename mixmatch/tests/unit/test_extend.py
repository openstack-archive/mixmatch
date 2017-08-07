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

import unittest
from mixmatch.extend.base import Route

class TestRoutes(unittest.TestCase):
    def setUp(self):
        pass

    def test_match_action_True(self):
        self.assertEqual(Route(None, None, None, [123, 'test'])._match_action([123, 'test']), True)
   
    def test_match_action_False(self):
        self.assertEqual(Route(None, None, None, [123, 'test'])._match_action([12, 'test']), False)
   
    def test_match_action_Different_Length(self):
        self.assertEqual(Route(None, None, None, [123, 'test', None])._match_action([123, 'test']), False)
        self.assertEqual(Route(None, None, None, [123, 'test'])._match_action([123, 'test', None]), False)


    def test_match_action_None(self):
        self.assertEqual(Route(None, None, None, None)._match_action([123]), True)
        self.assertEqual(Route(None, None, None, [123])._match_action(None), False)
        self.assertEqual(Route(None, None, None, None)._match_action(None), True)
if __name__=='__main__':
    unittest.main()
