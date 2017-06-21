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
    pip_install $MIXMATCH_DIR
}

function configure_mixmatch {
    # Proxy
    sudo mkdir -p /etc/mixmatch
    sudo chown $STACK_USER:$STACK_USER /etc/mixmatch
    cp $MIXMATCH_DIR/etc/mixmatch.conf.sample $MIXMATCH_CONF

    iniset $MIXMATCH_CONF database connection "sqlite:////tmp/mixmatch.db"
    iniset $MIXMATCH_CONF DEFAULT port $MIXMATCH_SERVICE_PORT
    iniset $MIXMATCH_CONF DEFAULT service_providers default
    iniset $MIXMATCH_CONF DEFAULT aggregation False

    iniset $MIXMATCH_CONF auth auth_url "$KEYSTONE_AUTH_URI/v3"
    iniset $MIXMATCH_CONF auth username admin
    iniset $MIXMATCH_CONF auth user_domain_id default
    iniset $MIXMATCH_CONF auth project_name admin
    iniset $MIXMATCH_CONF auth project_domain_id default
    iniset $MIXMATCH_CONF auth password $ADMIN_PASSWORD

    iniset $MIXMATCH_CONF sp_default sp_name default
    iniset $MIXMATCH_CONF sp_default auth_url "$KEYSTONE_AUTH_URI/v3"
    iniset $MIXMATCH_CONF sp_default image_endpoint \
        "$GLANCE_SERVICE_PROTOCOL://$GLANCE_HOSTPORT"
    iniset $MIXMATCH_CONF sp_default volume_endpoint \
        "$CINDER_SERVICE_PROTOCOL://$CINDER_SERVICE_HOST:$CINDER_SERVICE_PORT"

    run_process mixmatch "uwsgi $MIXMATCH_DIR/httpd/mixmatch-uwsgi.ini"

    # Nova
    iniset $NOVA_CONF glance api_servers "$MIXMATCH_SERVICE_PROTOCOL://$HOST_IP:$MIXMATCH_SERVICE_PORT/image"

    # Cinder
    iniset $CINDER_CONF DEFAULT glance_api_servers \
        "$MIXMATCH_SERVICE_PROTOCOL://$HOST_IP:$MIXMATCH_SERVICE_PORT/image"
    iniset $CINDER_CONF oslo_messaging_notifications driver messaging
    iniset $CINDER_CONF oslo_messaging_notifications topics notifications

    # Glance
    iniset $GLANCE_CONF oslo_messaging_notifications driver messaging
    iniset $CINDER_CONF oslo_messaging_notifications topics notifications
    
    # Copy apache config
    # FIXME(knikolla): Where's the directory
    sudo cp "$MIXMATCH_DIR/httpd/mixmatch-uwsgi.conf" $(apache_site_config_for mixmatch)
    restart_apache_server
}
