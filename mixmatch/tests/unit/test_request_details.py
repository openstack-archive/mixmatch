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

from mixmatch import proxy


class TestRequestDetails(testcase.TestCase):

    def test_capitalized_headers(self):
        normal_headers = {"Mm-Service-Provider": "default",
                          "X-Auth-Token": "tok",
                          "Transfer-Encoding": "chunked"}
        with proxy.app.test_request_context():
            rd = proxy.RequestDetails("GET", "image/v2/images", normal_headers)
        expected = {"MM-PROXY-IP-LIST": 'localhost',
                    "MM-SERVICE-PROVIDER": "default",
                    "X-AUTH-TOKEN": "tok",
                    "TRANSFER-ENCODING": "chunked"}
        self.assertEqual(expected, rd.headers)

    def test_proxy_list_append(self):
        normal_headers = {"Mm-Service-Provider": "default",
                          "X-Auth-Token": "tok",
                          "Transfer-Encoding": "chunked",
                          "MM-PROXY-IP-LIST": "1.1.1.1"}
        with proxy.app.test_request_context():
            rd = proxy.RequestDetails("GET", "image/v2/images", normal_headers)
        expected = {"MM-PROXY-IP-LIST": "1.1.1.1,localhost",
                    "MM-SERVICE-PROVIDER": "default",
                    "X-AUTH-TOKEN": "tok",
                    "TRANSFER-ENCODING": "chunked"}
        self.assertEqual(expected, rd.headers)
