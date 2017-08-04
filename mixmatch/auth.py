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
import os

try:
    from urllib.parse import urlparse, urlunparse
except ImportError:
    from urlparse import urlparse, urlunparse


from flask import abort

from mixmatch import config
from mixmatch import utils

CONF = config.CONF
LOG = config.LOG

MEMOIZE_SESSION = config.auth.MEMOIZE


@MEMOIZE_SESSION
def get_admin_session():
    """Return a Keystone session using admin service credentials."""
    LOG.info("Getting Admin Session")
    service_auth = identity.Password(
        auth_url=CONF.auth.auth_url,
        username=CONF.auth.username,
        password=CONF.auth.password,
        project_name=CONF.auth.project_name,
        project_domain_id=CONF.auth.project_domain_id,
        user_domain_id=CONF.auth.user_domain_id
    )
    local_session = session.Session(auth=service_auth)

    return local_session


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


def _trim_endpoint(endpoint):
    """Removes the project_id and version from the endpoint."""
    endpoint = list(urlparse(endpoint))  # type: urlparse.ParseResult
    # Note(knikolla): Elements are in order 'scheme, netloc, path'
    path = endpoint[2].split('/')
    utils.pop_tail_if_uuid(path)
    # FIXME(knikolla): Write proper regex
    if utils.safe_get(path, -1) in ['v1', 'v2', 'v3']:
        path.pop(-1)
    endpoint[2] = os.path.join(*path)

    return urlunparse(endpoint)


def _get_conf_endpoint(sp, service):
    """Return an endpoint for a service in conf."""
    conf = config.service_providers.get(CONF, sp)
    endpoint = None

    if service == 'image':
        endpoint = conf.image_endpoint
    elif service == 'volume':
        endpoint = conf.volume_endpoint
    elif service == 'network':
        endpoint = conf.network_endpoint

    return endpoint


@MEMOIZE_SESSION
def get_sp_endpoint(sp, service, version):
    """Return an endpoint for a service."""
    endpoint = _get_conf_endpoint(sp, service)

    # If endpoint is not in conf, it will try to discover it
    if endpoint is None:
        if sp == 'default':
            LOG.error('No service url configured for (%s, %s)'
                      % (sp, service))
            raise
        else:
            admin_session = get_admin_session()
            token = admin_session.get_token()
            project_id = get_projects_at_sp(sp,
                                            token)[0]
            auth_session = get_sp_auth(sp, token, project_id)
            endpoint = auth_session.get_endpoint(service_type=service,
                                                 interface='publicURL',
                                                 min_version=version,
                                                 max_version=version)
            if endpoint is None:
                LOG.error('No service url configured for (%s, %s)'
                          % (sp, service))
                raise

    endpoint = _trim_endpoint(endpoint)
    return endpoint
