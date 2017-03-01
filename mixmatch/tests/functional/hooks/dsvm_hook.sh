#!/bin/bash -xe

# Copyright 2017 Massachusetts Open Cloud
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

function get_endpoint_ids {
    echo `openstack endpoint list --service $1 -c ID -f value`
}

function register_mixmatch {
    # Update the endpoints
    openstack endpoint delete `get_endpoint_ids image`
    openstack endpoint delete `get_endpoint_ids volume`
    openstack endpoint delete `get_endpoint_ids volumev2`
    openstack endpoint delete `get_endpoint_ids volumev3`

    get_or_create_endpoint \
        "image" \
        "$REGION_NAME" \
        "http://$HOST_IP:5001/image" \
        "http://$HOST_IP:5001/image" \
        "http://$HOST_IP:5001/image"

    get_or_create_endpoint \
        "volume" \
        "$REGION_NAME" \
        "http://$HOST_IP:5001/volume/v1/\$(project_id)s" \
        "http://$HOST_IP:5001/volume/v1/\$(project_id)s" \
        "http://$HOST_IP:5001/volume/v1/\$(project_id)s"

    get_or_create_endpoint \
        "volumev2" \
        "$REGION_NAME" \
        "http://$HOST_IP:5001/volume/v2/\$(project_id)s" \
        "http://$HOST_IP:5001/volume/v2/\$(project_id)s" \
        "http://$HOST_IP:5001/volume/v2/\$(project_id)s"

    get_or_create_endpoint \
        "volumev3" \
        "$REGION_NAME" \
        "http://$HOST_IP:5001/volume/v3/\$(project_id)s" \
        "http://$HOST_IP:5001/volume/v3/\$(project_id)s" \
        "http://$HOST_IP:5001/volume/v3/\$(project_id)s"
}

# Get admin credentials
cd $BASE/new/devstack
source openrc admin admin

register_mixmatch

# Run tempest API and scenario tests
cd $BASE/new/tempest

if [ -d .testrepository ]; then
    sudo rm -r .testrepository
fi

sudo chown -R jenkins:stack $BASE/new/tempest
sudo chown -R jenkins:stack /opt/stack/data/tempest

ostestr -r '(^tempest.api|^tempest.scenario)' --blacklist-file \
    $BASE/new/mixmatch/mixmatch/tests/functional/tempest_blacklist.txt

ostestr -r mixmatch_tempest_plugin
