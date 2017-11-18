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

MIXMATCH_BIN_DIR=$(get_python_exec_prefix)
MIXMATCH_CONF_DIR="/etc/mixmatch"

MIXMATCH_UWSGI_INI="$MIXMATCH_CONF_DIR/mixmatch-uwsgi.ini"

function install_mixmatch {
    pip_install $MIXMATCH_DIR
}

function configure_mixmatch {
    # Proxy
    sudo mkdir -p /etc/mixmatch
    sudo chown $STACK_USER:$STACK_USER /etc/mixmatch
    cp $MIXMATCH_DIR/etc/mixmatch.conf.sample $MIXMATCH_CONF
    cp $MIXMATCH_DIR/etc/api-paste.ini $MIXMATCH_CONF_DIR

    iniset $MIXMATCH_CONF database connection "sqlite:////tmp/mixmatch.db"
    iniset $MIXMATCH_CONF DEFAULT service_providers default
    iniset $MIXMATCH_CONF DEFAULT aggregation False

    iniset $MIXMATCH_CONF auth auth_url "$KEYSTONE_AUTH_URI/v3"
    iniset $MIXMATCH_CONF auth username admin
    iniset $MIXMATCH_CONF auth user_domain_id default
    iniset $MIXMATCH_CONF auth project_name admin
    iniset $MIXMATCH_CONF auth project_domain_id default
    iniset $MIXMATCH_CONF auth password $ADMIN_PASSWORD

    iniset $MIXMATCH_CONF keystone_authtoken auth_plugin password
    iniset $MIXMATCH_CONF keystone_authtoken auth_url "$KEYSTONE_AUTH_URI/v3"
    iniset $MIXMATCH_CONF keystone_authtoken project_name admin
    iniset $MIXMATCH_CONF keystone_authtoken username admin
    iniset $MIXMATCH_CONF keystone_authtoken password "$ADMIN_PASSWORD"
    iniset $MIXMATCH_CONF keystone_authtoken user_domain_name "$SERVICE_DOMAIN_NAME"
    iniset $MIXMATCH_CONF keystone_authtoken project_domain_name "$SERVICE_DOMAIN_NAME"

    iniset $MIXMATCH_CONF sp_default sp_name default
    iniset $MIXMATCH_CONF sp_default auth_url "$KEYSTONE_AUTH_URI/v3"
    iniset $MIXMATCH_CONF sp_default image_endpoint $GLANCE_URL

    CINDER_BASE="$CINDER_SERVICE_PROTOCOL://$CINDER_SERVICE_HOST"
    if [ "$CINDER_USE_MOD_WSGI" == "True" ]; then
        CINDER_URL="$CINDER_BASE/volume"
    else
        CINDER_URL="$CINDER_BASE:$CINDER_SERVICE_PORT"
    fi

    iniset $MIXMATCH_CONF sp_default volume_endpoint $CINDER_URL
    iniset $MIXMATCH_CONF sp_default network_endpoint \
        "$NEUTRON_SERVICE_PROTOCOL://$NEUTRON_SERVICE_HOST:$NEUTRON_SERVICE_PORT"
    iniset $MIXMATCH_CONF sp_default enabled_services "image, volume, network"

    # Nova
    iniset $NOVA_CONF glance api_servers "$MIXMATCH_URL/proxied/image"
    iniset $NOVA_CONF neutron url "$MIXMATCH_URL/proxied/network"

    # Cinder
    iniset $CINDER_CONF DEFAULT glance_api_servers "$MIXMATCH_URL/proxied/image"
    iniset $CINDER_CONF oslo_messaging_notifications driver messaging
    iniset $CINDER_CONF oslo_messaging_notifications topics notifications

    # Glance
    iniset $GLANCE_CONF oslo_messaging_notifications driver messaging
    iniset $CINDER_CONF oslo_messaging_notifications topics notifications

    mixmatch-manage db_sync

    sudo cp $MIXMATCH_DIR/httpd/mixmatch-uwsgi.conf $(apache_site_config_for mixmatch)
    enable_apache_site mixmatch
    restart_apache_server

    run_process mixmatch \
        "$MIXMATCH_BIN_DIR/uwsgi --ini $MIXMATCH_DIR/httpd/mixmatch-uwsgi.ini"
}

function get_endpoint_ids {
    echo `openstack endpoint list --service $1 -c ID -f value`
}

function register_mixmatch {
    if [ "$REGISTER_MIXMATCH" == "true" ]; then
        # Update the endpoints
        openstack endpoint delete `get_endpoint_ids image`
        openstack endpoint delete `get_endpoint_ids volume`
        openstack endpoint delete `get_endpoint_ids volumev2`
        openstack endpoint delete `get_endpoint_ids volumev3`
        openstack endpoint delete `get_endpoint_ids network`

        get_or_create_endpoint \
            "image" \
            "$REGION_NAME" \
            "$MIXMATCH_URL/proxied/image" \
            "$MIXMATCH_URL/proxied/image" \
            "$MIXMATCH_URL/proxied/image"

        get_or_create_endpoint \
            "volume" \
            "$REGION_NAME" \
            "$MIXMATCH_URL/proxied/volume/v1/\$(project_id)s" \
            "$MIXMATCH_URL/proxied/volume/v1/\$(project_id)s" \
            "$MIXMATCH_URL/proxied/volume/v1/\$(project_id)s"

        get_or_create_endpoint \
            "volumev2" \
            "$REGION_NAME" \
            "$MIXMATCH_URL/proxied/volume/v2/\$(project_id)s" \
            "$MIXMATCH_URL/proxied/volume/v2/\$(project_id)s" \
            "$MIXMATCH_URL/proxied/volume/v2/\$(project_id)s"

        get_or_create_endpoint \
            "volumev3" \
            "$REGION_NAME" \
            "$MIXMATCH_URL/proxied/volume/v3/\$(project_id)s" \
            "$MIXMATCH_URL/proxied/volume/v3/\$(project_id)s" \
            "$MIXMATCH_URL/proxied/volume/v3/\$(project_id)s"

        get_or_create_endpoint \
            "network" \
            "$REGION_NAME" \
            "$MIXMATCH_URL/proxied/network" \
            "$MIXMATCH_URL/proxied/network" \
            "$MIXMATCH_URL/proxied/network"
    fi
}
