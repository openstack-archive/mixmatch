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
source $MIXMATCH_PLUGIN/mixmatch.sh

# For more information on Devstack plugins, including a more detailed
# explanation on when the different steps are executed please see:
# https://docs.openstack.org/developer/devstack/plugins.html

if [[ "$1" == "stack" && "$2" == "install" ]]; then
    # This phase is executed after the projects have been installed
    echo "Mix & match plugin - Install phase"
    if is_service_enabled mixmatch; then
        install_mixmatch
    fi

    if [[ "MIXMATCH_MULTINODE" == "true" ]]; then
        if is_service_enabled keystone-idp; then
            :
        fi

        # Note(knikolla): If keystone federation is enabled, then we're
        # one of the service providers. In the case of a multinode CI
        # environment, that means we're the subnode, so we should
        # point the keystone plugin to federate with the primary node.
        if is_service_enabled keystone-saml2-federation; then
            override_keystone_configs
        fi
    fi

elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
    # This phase is executed after the projects have been configured and
    # before they are started
    echo "Mix & match plugin - Post-config phase"
    if is_service_enabled mixmatch; then
        configure_mixmatch
    fi


elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
    # This phase is executed after the projects have been started
    echo "Mix & match plugin - Extra phase"
    if is_service_enabled mixmatch; then
        register_mixmatch
    fi

    if [[ "MIXMATCH_MULTINODE" == "true" ]]; then
        # Note(knikolla): If keystone as an idp is enabled, we're the
        # primary node and we should federate with the subnode.
        if is_service_enabled keystone-idp; then
            register_sp
        fi

        # Note(knikolla): If keystone federation is enabled, then we're
        # one of the service providers. In the case of a multinode CI
        # environment, that means we're the subnode, so we should
        # point the keystone plugin to federate with the primary node.
        if is_service_enabled keystone-saml2-federation; then
            register_idp
        fi
    fi
fi

if [[ "$1" == "unstack" ]]; then
    # Called by unstack.sh and clean.sh
    # Undo what was performed during the "post-config" and "extra" phases
    :
fi

if [[ "$1" == "clean" ]]; then
    # Called by clean.sh after the "unstack" phase
    # Undo what was performed during the "install" phase
    :
fi
