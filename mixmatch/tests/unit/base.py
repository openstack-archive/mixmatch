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

import oslo_db
import fixtures
import uuid

from testtools import testcase
from six.moves.urllib import parse
from requests_mock.contrib import fixture as requests_fixture
from oslo_config import fixture as config_fixture

from mixmatch import config
from mixmatch import extend
from mixmatch.proxy import app
from mixmatch.model import BASE, enginefacade

CONF = config.CONF


class BaseTest(testcase.TestCase):
    def setUp(self):
        super(BaseTest, self).setUp()
        self.requests_fixture = self.useFixture(requests_fixture.Fixture())
        self.config_fixture = self.useFixture(config_fixture.Config(conf=CONF))
        self.session_fixture = self.useFixture(SessionFixture())
        self.db_fixture = self.useFixture(DatabaseFixture(conf=CONF))
        self.app = app.test_client()

        self.service_providers = {
            'default': {
                'image_endpoint': 'http://images.local',
                'volume_endpoint': 'http://volumes.local'
            },
            'remote1': {
                'image_endpoint': 'http://images.remote1',
                'volume_endpoint': 'http://volumes.remote1'
            },
        }

        self.auth = FakeSession(token=uuid.uuid4().hex,
                                project=uuid.uuid4().hex,
                                sp=self.service_providers['default'])
        self.remote_auth = FakeSession(token=uuid.uuid4().hex,
                                       project=uuid.uuid4().hex,
                                       sp=self.service_providers['remote1'])

        # set config values
        self.config_fixture.load_raw_values(
            service_providers='default, remote1',
            aggregation=True)
        self.config_fixture.load_raw_values(
            group='sp_default',
            image_endpoint='http://images.local',
            volume_endpoint='http://volumes.local')
        self.config_fixture.load_raw_values(
            group='sp_remote1',
            image_endpoint='http://images.remote1',
            volume_endpoint='http://volumes.remote1')
        config.post_config()
        extend.load_extensions()

    def load_auth_fixtures(self):
        self.session_fixture.add_local_auth(self.auth)
        self.session_fixture.add_sp_auth('remote1',
                                         self.auth.get_token(),
                                         self.remote_auth)
        self.session_fixture.add_project_at_sp(
            'remote1', self.remote_auth.get_project_id())


class FakeSession(object):
    """A replacement for keystoneauth1.session.Session."""
    def __init__(self, token=None, project=None, sp=None):
        self.token = token
        self.project = project
        self.sp = sp

    def get_token(self):
        return self.token

    def get_project_id(self):
        return self.project

    def get_headers(self):
        return {'X-AUTH-TOKEN': self.token,
                'CONTENT-TYPE': 'application/json'}

    def get_endpoint(self, **kwargs):
        if kwargs['service_type'] == 'image':
            return self.sp['image_endpoint']
        elif kwargs['service_type'] == 'volume':
            return self.sp['volume_endpoint']


class SessionFixture(fixtures.Fixture):
    """A fixture that mocks get_{sp,local}_session."""
    def _setUp(self):
        def get_local_auth(token):
            return self.local_auths[token]

        def get_sp_auth(sp, token, project):
            return self.sp_auths[(sp, token, project)]

        def get_projects_at_sp(sp, token):
            if sp in self.sp_projects:
                return self.sp_projects[sp]
            else:
                return []

        def get_admin_session():
            token, project = next(iter(self.local_auths.items()))
            return FakeSession(token, project)

        self.local_auths = {}
        self.sp_auths = {}
        self.sp_projects = {}
        self.useFixture(fixtures.MonkeyPatch(
            'mixmatch.auth.get_sp_auth', get_sp_auth))
        self.useFixture(fixtures.MonkeyPatch(
            'mixmatch.auth.get_local_auth', get_local_auth))
        self.useFixture(fixtures.MonkeyPatch(
            'mixmatch.auth.get_projects_at_sp', get_projects_at_sp))
        self.useFixture(fixtures.MonkeyPatch(
            'mixmatch.auth.get_admin_session', get_admin_session))

    def add_local_auth(self, session):
        self.local_auths[session.get_token()] = session

    def add_sp_auth(self, sp, token, remote_session):
        self.sp_auths[(sp, token, remote_session.get_project_id())] = remote_session

    def add_project_at_sp(self, sp, project):
        if sp in self.sp_projects:
            self.sp_projects[sp].append(project)
        else:
            self.sp_projects[sp] = [project]


class DatabaseFixture(fixtures.Fixture):
    """A fixture that performs each test in a new, blank database."""
    def __init__(self, conf):
        super(DatabaseFixture, self).__init__()
        oslo_db.options.set_defaults(conf, connection="sqlite://")

    def _setUp(self):
        context = enginefacade.transaction_context()
        with enginefacade.writer.using(context) as session:
            self.engine = session.get_bind()
        BASE.metadata.create_all(bind=self.engine)
        self.addCleanup(BASE.metadata.drop_all, bind=self.engine)

    def recreate(self):
        BASE.metadata.create_all(bind=self.engine)


# Source: http://stackoverflow.com/a/9468284
class Url(object):
    """Url object that can be compared with other url objects

    This comparison is done without regard to the vagaries of encoding,
    escaping, and ordering of parameters in query strings.
    """

    def __init__(self, url):
        parts = parse.urlparse(url)
        _query = frozenset(parse.parse_qsl(parts.query))
        _path = parse.unquote_plus(parts.path)
        parts = parts._replace(query=_query, path=_path)
        self.parts = parts

    def __eq__(self, other):
        return self.parts == other.parts

    def __hash__(self):
        return hash(self.parts)
