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

source $MIXMATCH_PLUGIN/keystone.sh

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

    iniset $MIXMATCH_CONF database connection "sqlite:////tmp/mixmatch.db"

    iniset $MIXMATCH_CONF DEFAULT aggregation False

    if [ "$MIXMATCH_MULTINODE" == "true" ]; then
        iniset $MIXMATCH_CONF DEFAULT service_providers "default, sp"
    else
        iniset $MIXMATCH_CONF DEFAULT service_providers "default"
    fi

    iniset $MIXMATCH_CONF auth auth_url "$KEYSTONE_AUTH_URI/v3"
    iniset $MIXMATCH_CONF auth username admin
    iniset $MIXMATCH_CONF auth user_domain_id default
    iniset $MIXMATCH_CONF auth project_name admin
    iniset $MIXMATCH_CONF auth project_domain_id default
    iniset $MIXMATCH_CONF auth password $ADMIN_PASSWORD

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
    iniset $NOVA_CONF glance api_servers "$MIXMATCH_URL/image"
    iniset $NOVA_CONF neutron url "$MIXMATCH_URL/network"

    # Cinder
    iniset $CINDER_CONF DEFAULT glance_api_servers "$MIXMATCH_URL/image"
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

function register_mixmatch {
    if [ "$REGISTER_MIXMATCH" == "true" ]; then
        # Update the endpoints
        recreate_endpoints image
        recreate_endpoints volume
        recreate_endpoints volumev2
        recreate_endpoints volumev3
        recreate_endpoints network
    fi
}
