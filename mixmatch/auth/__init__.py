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

from flask import abort
from keystoneauth1 import identity
from keystoneauth1 import session
from keystoneclient import v3
from keystoneauth1.exceptions import http
from stevedore import driver

from mixmatch.auth import base
from mixmatch import config

CONF = config.CONF
LOG = config.LOG

MEMOIZE_SESSION = config.auth.MEMOIZE

DRIVERS = dict()  # type: dict(str, base:AuthDriver)
for sp in CONF.service_providers:
    DRIVERS[sp] = driver.DriverManager(
        namespace='mixmatch.auth.driver',
        name=CONF.service_providers.get(CONF, sp).auth,
        invoke_on_load=True,
        invoke_args=(sp,)
    )


@MEMOIZE_SESSION
def get_client():
    """Return a Keystone client capable of validating tokens."""
    LOG.info("Getting Admin Client")
    service_auth = identity.Password(
        auth_url=CONF.auth.auth_url,
        username=CONF.auth.username,
        password=CONF.auth.password,
        project_name=CONF.auth.project_name,
        project_domain_id=CONF.auth.project_domain_id,
        user_domain_id=CONF.auth.user_domain_id
    )
    local_session = session.Session(auth=service_auth)
    return v3.client.Client(session=local_session)


@MEMOIZE_SESSION
def get_local_auth(user_token):
    """Return a Keystone session for the local cluster."""
    LOG.debug("Getting session for %s" % user_token)
    client = get_client()
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
def get_projects_at_sp(service_provider, user_token):
    """Return projects of the user at the service provider.
    
    :type service_provider: str
    :type user_token: str
    :return: List[str]
    """
    return DRIVERS[service_provider].get_projects_at_sp(user_token)


@MEMOIZE_SESSION
def get_sp_auth(service_provider, user_token, remote_project):
    """
    
    :type service_provider: str
    :type user_token: str
    :type remote_project: str
    :rtype: session:Session
    """
    return DRIVERS[service_provider].get_sp_auth(user_token, remote_project)
