#   Copyright 2017 Massachusetts Open Cloud
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

import re

from mixmatch import auth
from mixmatch.config import CONF, service_providers
from mixmatch.extend import base
from mixmatch import utils

import flask
from neutronclient.v2_0 import client as neutron
from neutronclient.common import exceptions as n_ex
from oslo_serialization import jsonutils


class ExtendNetwork(base.Extension):
    """An extension which smells like POST /networks.

    It performs some privileged operations related to setting VXLAN ID, and
    also optionally manages some subnet stuff.

    For now it is ENTIRELY OPTIMIZED, but that will be fixed when the logic is
    moved out of an extension and built into an explict API of a new service.
    """

    ROUTES = [
        ('/network/v2.0/networks/extended', ['POST']),
        # For now, mask POST /networks. Later, move the extend-network logic
        # into a new API.
    ]

    def handle_request(self, request):
        body = jsonutils.loads(request.body)

        origin_sp = utils.safe_get(request.headers, 'MM-SERVICE-PROVIDER')
        existing_net_id = utils.safe_pop(body['network'], 'existing_net')
        should_mangle_subnet = utils.safe_pop(
            body['network'], 'give_me_a_subnet', False
        )

        if origin_sp is None or existing_net_id is None:
            flask.abort(400)
        enabled_sps = filter(
            lambda sp: (request.service in
                        service_providers.get(CONF, sp).enabled_services),
            CONF.service_providers
        )
        if origin_sp not in enabled_sps:
            flask.abort(422)

        remote_admin_session = auth.get_admin_session(origin_sp)
        remote_neutronclient = neutron.Client(session=remote_admin_session)
        try:
            original = remote_neutronclient.show_network(existing_net_id)
        except n_ex.NeutronClientException:
            flask.abort(422)
        remote_project_ids = auth.get_projects_at_sp(
            origin_sp, request.token)
        if original['network']['project_id'] not in remote_project_ids:
            flask.abort(403)

        body['network']['provider:network_type'] = 'vxlan'
        vxlan_id = original['network']['provider:segmentation_id']
        body['network']['provider:segmentation_id'] = vxlan_id
        local_project_id = auth.get_local_auth(request.token).get_project_id()
        body['network']['project_id'] = local_project_id

        local_neutronclient = (
            neutron.Client(session=auth.get_admin_session())
        )
        try:
            new_net = local_neutronclient.create_network(body)
        except n_ex.Conflict:
            # ultimately we should have a way of avoiding conflict in the
            # first place, or properly react to it by choosing a new VXLAN ID
            # ... also, this conflict could be "network name in use" too!
            flask.abort(500)
        except n_ex.NeutronClientException:
            flask.abort(503)

        if should_mangle_subnet:
            # the logic here gets messy quick. we can consider leaving this
            # responsibility to the user.
            try:
                old_subnet = (
                    [s for s in remote_neutronclient.list_subnets()['subnets']
                     if (s['ip_version'] == 4 and
                         s['network_id'] == existing_net_id)][0]
                )
                old_subnet_id = old_subnet['id']
                old_subnet_start = old_subnet['allocation_pools'][0]['start']
                maximum_ip = int(
                    old_subnet['allocation_pools'][0]['end']
                    .split('.')[-1]
                )
                pool_base = re.sub(r'\d+$', '', old_subnet_start)
                remote_neutronclient.update_subnet(
                    old_subnet_id, body={'subnet': {'allocation_pools':
                                         [{'start': old_subnet_start,
                                           'end': '{}{}'.format(
                                               pool_base, maximum_ip // 2)}]}}
                )
                new_subnet_body = (
                    {'project_id': local_project_id,
                     'enable_dhcp': False,
                     'network_id': new_net['network']['id'],
                     'dns_nameservers': old_subnet['dns_nameservers'],
                     'ip_version': 4,
                     'gateway_ip': old_subnet['gateway_ip'],
                     'cidr': old_subnet['cidr'],
                     'allocation_pools':
                     [{'start': '{}{}'.format(pool_base, maximum_ip // 2 + 1),
                       'end': '{}{}'.format(pool_base, maximum_ip)}]
                     }
                )
                new_subnet = local_neutronclient.create_subnet(
                    body={'subnet': new_subnet_body})
                new_net['network']['subnets'].append(
                    new_subnet['subnet']['id'])
            except n_ex.NeutronClientException:
                local_neutronclient.delete_network(new_net['network']['id'])
                flask.abort(500)

        return base.FinalResponse(
            jsonutils.dumps(new_net),
            201,
            headers={'Content-Type': 'application/json'}
        )
