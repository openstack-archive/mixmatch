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

from mixmatch import auth
from mixmatch.config import CONF
from mixmatch.extend import base
from mixmatch import utils

import flask
from neutronclient.v2_0 import client as neutron
from neutronclient.common import exceptions as n_ex
from oslo_serialization import jsonutils


class ExtendNetwork(base.Extension):
    """An extension which smells like Neutron's POST /networks.

    It performs some privileged operations related to setting VXLAN ID, and
    also optionally manages some subnet stuff.
    """

    ROUTES = [
        ('/network/v2.0/networks/extended', ['POST']),
        # For now, mask POST /networks. Later, move the extend-network logic
        # into a new API.
    ]

    def handle_request(self, request):
        body = jsonutils.loads(request.body)

        origin_sp = utils.safe_pop(body['network'], 'existing_net_sp')
        existing_net_id = utils.safe_pop(body['network'], 'existing_net_id')

        if origin_sp is None or existing_net_id is None:
            flask.abort(400)
        if origin_sp not in CONF.service_providers:
            flask.abort(422)

        remote_admin_session = auth.get_admin_session(origin_sp)
        remote_neutronclient = neutron.Client(session=remote_admin_session)
        try:
            original = remote_neutronclient.show_network(existing_net_id)
        except n_ex.NeutronClientException as e:
            raise
            flask.abort(422 if e.status_code < 500 else 503)
        remote_project_ids = auth.get_projects_at_sp(
            origin_sp, request.token)
        if original['network']['project_id'] not in remote_project_ids:
            flask.abort(403)

        local_user_session = auth.get_local_auth(request.token)
        local_user_neutronclient = neutron.Client(session=local_user_session)

        try:
            new_net_id = (
                local_user_neutronclient.create_network(body)['network']['id']
            )
        except n_ex.Conflict:
            # Conflict could happen when names collide. So, give client error.
            flask.abort(409)
        except n_ex.NeutronClientException:
            raise
            flask.abort(503)

        local_admin_session = auth.get_admin_session()
        local_admin_neutronclient = (
            neutron.Client(session=local_admin_session)
        )

        privileged_attrs = {'network': {}}
        privileged_attrs['network']['provider:network_type'] = 'vxlan'
        vxlan_id = original['network']['provider:segmentation_id']
        privileged_attrs['network']['provider:segmentation_id'] = vxlan_id

        try:
            final_net = local_admin_neutronclient.update_network(
                new_net_id, privileged_attrs)
        except n_ex.NeutronClientException:
            raise
            flask.abort(503)

        return base.FinalResponse(
            jsonutils.dumps(final_net),
            201,
            headers={'Content-Type': 'application/json'}
        )
