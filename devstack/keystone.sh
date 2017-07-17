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

function recreate_endpoint {
    openstack endpoint delete `get_endpoint_ids $1`

    get_or_create_endpoint $1 "$REGION_NAME" $2 $2 $2
}

function register_sp {
    local sp_url="http://$1/Shibboleth.sso/SAML2/ECP"
    local auth_url="http://$1/identity/v3/OS-FEDERATION/identity_providers/myidp/protocols/mapped/auth"

    openstack service provider create sp \
        --sevice-provider-url $sp_url \
        --auth_url $auth_url
}

function register_idp {
    openstack identity provider create --remote-id $1 idp

    openstack mapping create --rules $MIXMATCH_FILES/mapping.json mapping

    openstack federation protocol create --identity-provider idp --mapping mapping mapped
}
