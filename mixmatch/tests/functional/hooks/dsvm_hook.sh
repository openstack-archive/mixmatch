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

# Get admin credentials
cd $BASE/new/devstack
source openrc admin admin

# Register the endpoints
source $BASE/new/mixmatch/devstack/settings
source $BASE/new/mixmatch/devstack/mixmatch.sh
REGISTER_MIXMATCH=true
register_mixmatch

# Restart Nova and Cinder so they use the proxy endpoints
sudo systemctl restart devstack@n-*
sudo systemctl restart devstack@c-*

# Run tempest API and scenario tests
cd $BASE/new/tempest

if [ -d .testrepository ]; then
    sudo rm -r .testrepository
fi

sudo chown -R $USER:stack $BASE/new/tempest
sudo chown -R $USER:stack /opt/stack/data/tempest

ostestr -r '(^tempest.api.compute|^tempest.api.volume|^tempest.scenario)' \
    --blacklist-file $BASE/new/mixmatch/mixmatch/tests/functional/tempest_blacklist.txt
