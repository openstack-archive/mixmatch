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

CONF = config.CONF
LOG = config.LOG

MEMOIZE_SESSION = config.auth.MEMOIZE


class _TargetedSession(session.Session):
    def __init__(self, sp, *args, **kwargs):
        super(_TargetedSession, self).__init__(*args, **kwargs)
        self.sp = sp

    def get_auth_headers(self, auth=None, **kwargs):
        headers = super(_TargetedSession, self).get_auth_headers()
        headers["MM-SERVICE-PROVIDER"] = self.sp
        return headers


@MEMOIZE_SESSION
def get_admin_session(sp=None):
    """Return a Keystone session using admin service credentials."""
    LOG.info("Getting Admin Session")
    if sp == "cloud2":
        service_auth = identity.Password(
            auth_url="http://10.19.97.9/identity",
            username="admin",
            password="nomoresecret",
            project_name="admin",
            project_domain_id="default",
            user_domain_id="default"
        )
        return _TargetedSession(sp, auth=service_auth)
    else:
        service_auth = identity.Password(
            auth_url=CONF.auth.auth_url,
            username=CONF.auth.username,
            password=CONF.auth.password,
            project_name=CONF.auth.project_name,
            project_domain_id=CONF.auth.project_domain_id,
            user_domain_id=CONF.auth.user_domain_id
        )
        return session.Session(auth=service_auth)


@MEMOIZE_SESSION
def get_client(session):
    """Return a client object given a session object."""
    LOG.debug("Getting client for %s" % session)
    return v3.client.Client(session=session)


@MEMOIZE_SESSION
def get_local_auth(user_token):
    """Return a Keystone session for the local cluster."""
    LOG.debug("Getting session for %s" % user_token)
    admin_session = get_admin_session()
    client = get_client(admin_session)
    token = v3.tokens.TokenManager(client)

    try:
        token_data = token.validate(token=user_token, include_catalog=False)
    except http.NotFound:
        abort(401)

    project_id = token_data['project']['id']

    local_auth = identity.v3.Token(auth_url=CONF.auth.auth_url,
                                   token=user_token,
                                   project_id=project_id)

    return session.Session(auth=local_auth)


@MEMOIZE_SESSION
def get_unscoped_sp_auth(service_provider, user_token):
    """Perform K2K auth, and return an unscoped session."""
    conf = config.service_providers.get(CONF, service_provider)
    local_auth = get_local_auth(user_token).auth
    LOG.debug("Getting unscoped session for (%s, %s)" % (service_provider,
                                                         user_token))
    remote_auth = identity.v3.Keystone2Keystone(
        local_auth,
        conf.sp_name
    )
    return session.Session(auth=remote_auth)


def get_projects_at_sp(service_provider, user_token):
    """Perform K2K auth, and return the projects that can be scoped to."""
    if service_provider == "cloud2":
        return ["8a8b9956d7884ce59736e7d432c35c7a"]
    conf = config.service_providers.get(CONF, service_provider)
    unscoped_session = get_unscoped_sp_auth(service_provider, user_token)
    r = json.loads(str(unscoped_session.get(
        conf.auth_url + "/OS-FEDERATION/projects").text))
    return [project[u'id'] for project in r[u'projects']]


@MEMOIZE_SESSION
def get_sp_auth(service_provider, user_token, remote_project_id):
    """Perform K2K auth, and return a session for a remote cluster."""
    conf = config.service_providers.get(CONF, service_provider)
    local_auth = get_local_auth(user_token).auth

    LOG.debug("Getting session for (%s, %s, %s)" % (service_provider,
                                                    user_token,
                                                    remote_project_id))

    remote_auth = identity.v3.Keystone2Keystone(
        local_auth,
        conf.sp_name,
        project_id=remote_project_id
    )

    return session.Session(auth=remote_auth)
