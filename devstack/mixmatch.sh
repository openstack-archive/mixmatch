# Copyright 2016 Massachusetts Open Cloud
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

function install_mixmatch {
    cd $MIXMATCH_DIR
    pip_install -r requirements.txt
    sudo python setup.py install

    pip_install uwsgi
}

function configure_mixmatch {
    # Nova
    iniset $NOVA_CONF glance api_servers "http://$HOST_IP:$PROXY_PORT/image"

    # Cinder
    iniset $CINDER_CONF glance_api_servers "http://$HOST_IP:$PROXY_PORT/volume"
    iniset $CINDER_CONF oslo_messaging_notifications driver messaging
    iniset $CINDER_CONF oslo_messaging_notifications topics notifications

    # Glance
    iniset $GLANCE_CONF oslo_messaging_notifications driver messaging
    iniset $CINDER_CONF oslo_messaging_notifications topics notifications

    # Proxy
    sudo mkdir /etc/mixmatch
    sudo chown $STACK_USER:$STACK_USER /etc/mixmatch
    cp $MIXMATCH_DIR/etc/mixmatch.conf.sample $MIXMATCH_CONF

    iniset $MIXMATCH_CONF DEFAULT port $MIXMATCH_PORT
    iniset $MIXMATCH_CONF DEFAULT service_providers default

    iniset $MIXMATCH_CONF auth auth_url \
        "$KEYSTONE_SERVICE_PROTOCOL://$KEYSTONE_SERVICE_HOST:5000/v3"
    iniset $MIXMATCH_CONF auth username admin
    iniset $MIXMATCH_CONF auth user_domain_id default
    iniset $MIXMATCH_CONF auth project_name admin
    iniset $MIXMATCH_CONF auth project_domain_id default
    iniset $MIXMATCH_CONF auth password $ADMIN_PASSWORD

    iniset $MIXMATCH_CONF sp_default sp_name default
    iniset $MIXMATCH_CONF sp_default auth_url \
        "$KEYSTONE_SERVICE_PROTOCOL://$KEYSTONE_SERVICE_HOST:5000/v3"
    iniset $MIXMATCH_CONF sp_default image_endpoint \
        "$GLANCE_SERVICE_PROTOCOL://$GLANCE_HOSTPORT"
    iniset $MIXMATCH_CONF sp_default volume_endpoint \
        "$CINDER_SERVICE_PROTOCOL://$CINDER_SERVICE_HOST:$CINDER_SERVICE_PORT"
}

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
        "$MIXMATCH_SERVICE_PROTOCOL://$HOST_IP:$MIXMATCH_SERVICE_PORT/image" \
        "$MIXMATCH_SERVICE_PROTOCOL://$HOST_IP:$MIXMATCH_SERVICE_PORT/image" \
        "$MIXMATCH_SERVICE_PROTOCOL://$HOST_IP:$MIXMATCH_SERVICE_PORT/image"

    get_or_create_endpoint \
        "volume" \
        "$REGION_NAME" \
        "$MIXMATCH_SERVICE_PROTOCOL://$HOST_IP:$MIXMATCH_SERVICE_PORT/volume/v1/\$(project_id)s" \
        "$MIXMATCH_SERVICE_PROTOCOL://$HOST_IP:$MIXMATCH_SERVICE_PORT/volume/v1/\$(project_id)s" \
        "$MIXMATCH_SERVICE_PROTOCOL://$HOST_IP:$MIXMATCH_SERVICE_PORT/volume/v1/\$(project_id)s"

    get_or_create_endpoint \
        "volumev2" \
        "$REGION_NAME" \
        "$MIXMATCH_SERVICE_PROTOCOL://$HOST_IP:$MIXMATCH_SERVICE_PORT/volume/v2/\$(project_id)s" \
        "$MIXMATCH_SERVICE_PROTOCOL://$HOST_IP:$MIXMATCH_SERVICE_PORT/volume/v2/\$(project_id)s" \
        "$MIXMATCH_SERVICE_PROTOCOL://$HOST_IP:$MIXMATCH_SERVICE_PORT/volume/v2/\$(project_id)s"

    get_or_create_endpoint \
        "volumev3" \
        "$REGION_NAME" \
        "$MIXMATCH_SERVICE_PROTOCOL://$HOST_IP:$MIXMATCH_SERVICE_PORT/volume/v3/\$(project_id)s" \
        "$MIXMATCH_SERVICE_PROTOCOL://$HOST_IP:$MIXMATCH_SERVICE_PORT/volume/v3/\$(project_id)s" \
        "$MIXMATCH_SERVICE_PROTOCOL://$HOST_IP:$MIXMATCH_SERVICE_PORT/volume/v3/\$(project_id)s"

    # Run the proxy in a screen window
    run_process mixmatch "$MIXMATCH_DIR/run_proxy.sh"
}
