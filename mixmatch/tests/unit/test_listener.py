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
from oslo_messaging.notify import dispatcher as notify_dispatcher
import mock

from mixmatch.model import ResourceMapping
from mixmatch.listener import get_endpoints_for_sp


class TestListener(testcase.TestCase):
    @mock.patch('mixmatch.listener.insert')
    def test_create_volume(self, insert):
        endpoints = get_endpoints_for_sp('default')
        dispatcher = notify_dispatcher.NotificationDispatcher(
            endpoints, serializer=None)
        MESSAGE = {
          'payload': {
            'volume_id': "1232123212321",
            'tenant_id': "abdbabdbabdba"
          },
          'priority': 'info',
          'publisher_id': 'volume.node4',
          'event_type': 'volume.create.start',
          'timestamp': '2014-03-03 18:21:04.369234',
          'message_id': '99863dda-97f0-443a-a0c1-6ed317b7fd45'
        }
        incoming = mock.Mock(ctxt={}, message=MESSAGE)
        dispatcher.dispatch(incoming)
        insert.assert_called_with(
            ResourceMapping('volumes',
                            '1232123212321',
                            'abdbabdbabdba',
                            'default'))

    @mock.patch('mixmatch.listener.ResourceMapping.find', return_value=35)
    @mock.patch('mixmatch.listener.delete')
    def test_delete_volume(self, delete, find):
        endpoints = get_endpoints_for_sp('default')
        dispatcher = notify_dispatcher.NotificationDispatcher(
            endpoints, serializer=None)
        MESSAGE = {
          'payload': {
            'volume_id': "1232123212321",
            'tenant_id': "abdbabdbabdba"
          },
          'priority': 'info',
          'publisher_id': 'volume.node4',
          'event_type': 'volume.delete.end',
          'timestamp': '2014-03-03 18:21:04.369234',
          'message_id': '99863dda-97f0-443a-a0c1-6ed317b7fd45'
        }
        incoming = mock.Mock(ctxt={}, message=MESSAGE)
        dispatcher.dispatch(incoming)
        find.assert_called_with('volumes', '1232123212321')
        delete.assert_called_with(35)

    @mock.patch('mixmatch.listener.insert')
    def test_create_snapshot(self, insert):
        endpoints = get_endpoints_for_sp('default')
        dispatcher = notify_dispatcher.NotificationDispatcher(
            endpoints, serializer=None)
        MESSAGE = {
          'payload': {
            'snapshot_id': "1232123212321",
            'tenant_id': "abdbabdbabdba"
          },
          'priority': 'info',
          'publisher_id': 'snapshot.node4',
          'event_type': 'snapshot.create.start',
          'timestamp': '2014-03-03 18:21:04.369234',
          'message_id': '99863dda-97f0-443a-a0c1-6ed317b7fd45'
        }
        incoming = mock.Mock(ctxt={}, message=MESSAGE)
        dispatcher.dispatch(incoming)
        insert.assert_called_with(
            ResourceMapping('snapshots',
                            '1232123212321',
                            'abdbabdbabdba',
                            'default'))

    @mock.patch('mixmatch.listener.ResourceMapping.find', return_value=35)
    @mock.patch('mixmatch.listener.delete')
    def test_delete_snapshot(self, delete, find):
        endpoints = get_endpoints_for_sp('default')
        dispatcher = notify_dispatcher.NotificationDispatcher(
            endpoints, serializer=None)
        MESSAGE = {
          'payload': {
            'snapshot_id': "1232123212321",
            'tenant_id': "abdbabdbabdba"
          },
          'priority': 'info',
          'publisher_id': 'snapshot.node4',
          'event_type': 'snapshot.delete.end',
          'timestamp': '2014-03-03 18:21:04.369234',
          'message_id': '99863dda-97f0-443a-a0c1-6ed317b7fd45'
        }
        incoming = mock.Mock(ctxt={}, message=MESSAGE)
        dispatcher.dispatch(incoming)
        find.assert_called_with('snapshots', '1232123212321')
        delete.assert_called_with(35)

    @mock.patch('mixmatch.listener.insert')
    def test_create_image(self, insert):
        endpoints = get_endpoints_for_sp('default')
        dispatcher = notify_dispatcher.NotificationDispatcher(
            endpoints, serializer=None)
        MESSAGE = {
          'payload': {
            'id': "1232123212321",
            'owner': "abdbabdbabdba"
          },
          'priority': 'info',
          'publisher_id': 'image.node4',
          'event_type': 'image.create',
          'timestamp': '2014-03-03 18:21:04.369234',
          'message_id': '99863dda-97f0-443a-a0c1-6ed317b7fd45'
        }
        incoming = mock.Mock(ctxt={}, message=MESSAGE)
        dispatcher.dispatch(incoming)
        insert.assert_called_with(
            ResourceMapping('images',
                            '1232123212321',
                            'abdbabdbabdba',
                            'default'))

    @mock.patch('mixmatch.listener.ResourceMapping.find', return_value=35)
    @mock.patch('mixmatch.listener.delete')
    def test_delete_image(self, delete, find):
        endpoints = get_endpoints_for_sp('default')
        dispatcher = notify_dispatcher.NotificationDispatcher(
            endpoints, serializer=None)
        MESSAGE = {
          'payload': {
            'id': "1232123212321",
            'owner': "abdbabdbabdba"
          },
          'priority': 'info',
          'publisher_id': 'image.node4',
          'event_type': 'image.delete',
          'timestamp': '2014-03-03 18:21:04.369234',
          'message_id': '99863dda-97f0-443a-a0c1-6ed317b7fd45'
        }
        incoming = mock.Mock(ctxt={}, message=MESSAGE)
        dispatcher.dispatch(incoming)
        find.assert_called_with('images', '1232123212321')
        delete.assert_called_with(35)
