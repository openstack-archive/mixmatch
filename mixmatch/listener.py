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

import oslo_messaging

from mixmatch import config
from mixmatch.config import CONF, LOG
from mixmatch import model
from mixmatch.model import insert, delete, ResourceMapping

import eventlet
eventlet.monkey_patch()


class VolumeCreateEndpoint(object):
    filter_rule = oslo_messaging.NotificationFilter(
        publisher_id='^volume.*',
        event_type='^volume.create.start$')

    def __init__(self, sp_name):
        self.sp_name = sp_name

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.info('Creating volume mapping %s -> %s at %s' % (
                 payload['volume_id'],
                 payload['tenant_id'],
                 self.sp_name))
        insert(ResourceMapping("volumes",
               payload['volume_id'],
               payload['tenant_id'],
               self.sp_name))


class VolumeDeleteEndpoint(object):
    def __init__(self, sp_name):
        self.sp_name = sp_name
    filter_rule = oslo_messaging.NotificationFilter(
            publisher_id='^volume.*',
            event_type='^volume.delete.end$')

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.info('Deleting volume mapping %s -> %s at %s' % (
                 payload['volume_id'],
                 payload['tenant_id'],
                 self.sp_name))
        delete(ResourceMapping.find("volumes", payload['volume_id']))


class VolumeTransferEndpoint(object):
    filter_rule = oslo_messaging.NotificationFilter(
        publisher_id='^volume.*',
        event_type='^volume.transfer.accept.end$')

    def __init__(self, sp_name):
        self.sp_name = sp_name

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.info('Moving volume mapping %s -> %s at %s' % (
                 payload['volume_id'],
                 payload['tenant_id'],
                 self.sp_name))
        mapping = ResourceMapping.find("volumes", payload['volume_id'])
        # Since we're manually updating a field, we have to sanitize the UUID
        # ourselves.
        mapping.tenant_id = payload['tenant_id'].replace("-", "")


class SnapshotCreateEndpoint(object):
    filter_rule = oslo_messaging.NotificationFilter(
            publisher_id='^snapshot.*',
            event_type='^snapshot.create.start$')

    def __init__(self, sp_name):
        self.sp_name = sp_name

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.info('Creating snapshot mapping %s -> %s at %s' % (
                 payload['snapshot_id'],
                 payload['tenant_id'],
                 self.sp_name))
        insert(ResourceMapping("snapshots",
               payload['snapshot_id'],
               payload['tenant_id'],
               self.sp_name))


class SnapshotDeleteEndpoint(object):
    filter_rule = oslo_messaging.NotificationFilter(
        publisher_id='^snapshot.*',
        event_type='^snapshot.delete.end$')

    def __init__(self, sp_name):
        self.sp_name = sp_name

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.info('Deleting snapshot mapping %s -> %s at %s' % (
                 payload['snapshot_id'],
                 payload['tenant_id'],
                 self.sp_name))
        delete(ResourceMapping.find("snapshots", payload['snapshot_id']))


class ImageCreateEndpoint(object):
    filter_rule = oslo_messaging.NotificationFilter(
        publisher_id='^image.*',
        event_type='^image.create$')

    def __init__(self, sp_name):
        self.sp_name = sp_name

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.info('Creating image mapping %s -> %s at %s' % (
                 payload['id'],
                 payload['owner'],
                 self.sp_name))
        insert(ResourceMapping("images",
               payload['id'],
               payload['owner'],
               self.sp_name))


class ImageDeleteEndpoint(object):
    filter_rule = oslo_messaging.NotificationFilter(
        publisher_id='^image.*',
        event_type='^image.delete$')

    def __init__(self, sp_name):
        self.sp_name = sp_name

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.info('Deleting image mapping %s -> %s at %s' % (
                 payload['id'],
                 payload['owner'],
                 self.sp_name))
        delete(ResourceMapping.find("images", payload['id']))


def get_endpoints_for_sp(sp_name):
    return [
            VolumeCreateEndpoint(sp_name),
            VolumeDeleteEndpoint(sp_name),
            VolumeTransferEndpoint(sp_name),
            SnapshotCreateEndpoint(sp_name),
            SnapshotDeleteEndpoint(sp_name),
            ImageCreateEndpoint(sp_name),
            ImageDeleteEndpoint(sp_name)
    ]


def get_server_for_sp(sp):
    """Get notification listener for a particular service provider.

    The server can be run in the background under eventlet using .start()
    """
    cfg = config.get_conf_for_sp(sp)
    transport = oslo_messaging.get_notification_transport(CONF, cfg.messagebus)
    targets = [oslo_messaging.Target(topic='notifications')]
    return oslo_messaging.get_notification_listener(
            transport,
            targets,
            get_endpoints_for_sp(cfg.sp_name),
            executor='eventlet')


if __name__ == "__main__":
    config.load_config()
    config.more_config()
    model.create_tables()

    LOG.info("Now listening for changes")
    for sp in CONF.proxy.service_providers:
        get_server_for_sp(sp).start()
    while True:
        eventlet.sleep(5)
        # XXX do something moderately more intelligent than this...
