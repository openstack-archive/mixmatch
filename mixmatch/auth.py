#   Copyright 2016 Massachusetts Open Cloud
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

from keystoneauth1 import identity
from keystoneauth1 import session
from keystoneclient import v3
from keystoneauth1.exceptions import http

import json

from flask import abort

from mixmatch import config
from mixmatch.config import LOG, CONF, get_conf_for_sp


@config.MEMOIZE_SESSION
def get_client():
    """Return a Keystone client capable of validating tokens."""
    LOG.info("Getting Admin Client")
    service_auth = identity.Password(
        auth_url=CONF.keystone.auth_url,
        username=CONF.keystone.username,
        password=CONF.keystone.password,
        project_name=CONF.keystone.project_name,
        project_domain_id=CONF.keystone.project_domain_id,
        user_domain_id=CONF.keystone.user_domain_id
    )
    local_session = session.Session(auth=service_auth)
    return v3.client.Client(session=local_session)


@config.MEMOIZE_SESSION
def get_local_auth(user_token):
    """Return a Keystone session for the local cluster."""
    LOG.info("Getting session for %s" % user_token)
    client = get_client()
    token = v3.tokens.TokenManager(client)

    try:
        token_data = token.validate(token=user_token, include_catalog=False)
    except http.NotFound:
        abort(401)

    project_id = token_data['project']['id']

    local_auth = identity.v3.Token(auth_url=CONF.keystone.auth_url,
                                   token=user_token,
                                   project_id=project_id)

    return session.Session(auth=local_auth)


@config.MEMOIZE_SESSION
def get_unscoped_sp_auth(service_provider, user_token):
    """Perform K2K auth, and return an unscoped session."""
    conf = get_conf_for_sp(service_provider)
    local_auth = get_local_auth(user_token).auth
    LOG.info("Getting unscoped session for (%s, %s)" % (service_provider,
                                                        user_token))
    remote_auth = identity.v3.Keystone2Keystone(
        local_auth,
        conf.sp_name
    )
    return session.Session(auth=remote_auth)


def get_projects_at_sp(service_provider, user_token):
    """Perform K2K auth, and return the projects that can be scoped to."""
    conf = get_conf_for_sp(service_provider)
    unscoped_session = get_unscoped_sp_auth(service_provider, user_token)
    r = json.loads(str(unscoped_session.get(
        conf.auth_url + "/OS-FEDERATION/projects").text))
    return [project[u'id'] for project in r[u'projects']]


@config.MEMOIZE_SESSION
def get_sp_auth(service_provider, user_token, remote_project_id):
    """Perform K2K auth, and return a session for a remote cluster."""
    conf = get_conf_for_sp(service_provider)
    local_auth = get_local_auth(user_token).auth

    LOG.info("Getting session for (%s, %s, %s)" % (service_provider,
                                                   user_token,
                                                   remote_project_id))

    remote_auth = identity.v3.Keystone2Keystone(
        local_auth,
        conf.sp_name,
        project_id=remote_project_id
    )

    return session.Session(auth=remote_auth)
