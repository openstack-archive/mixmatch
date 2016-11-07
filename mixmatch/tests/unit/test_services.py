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

import json
from six.moves.urllib import parse
from oslo_config import fixture as config_fixture
from mixmatch.config import CONF

from testtools import testcase

from mixmatch import services
from mixmatch.tests.unit import samples


class Response:
    def __init__(self, text):
        self.text = text


# Source: http://stackoverflow.com/a/9468284
class Url(object):
    """A url object that can be compared with other url orbjects
    without regard to the vagaries of encoding, escaping, and ordering
    of parameters in query strings."""

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


VOLUMES = {'default': Response(json.dumps(samples.VOLUME_LIST_V2)),
           'sp1': Response(json.dumps(samples.VOLUME_LIST_V2))}

IMAGES = {'default': Response(json.dumps(samples.IMAGE_LIST_V2)),
          'sp1': Response(json.dumps(samples.IMAGE_LIST_V2_2))}

SMALLEST_IMAGE = '941882c5-b992-4fa9-bcba-9d25d2f4e3b8'
EARLIEST_IMAGE = '781b3762-9469-4cec-b58d-3349e5de4e9c'
SECOND_EARLIEST_IMAGE = '1bea47ed-f6a9-463b-b423-14b9cca9ad27'
LATEST_IMAGE = '61f655c0-4511-4307-a257-4162c87a5130'

IMAGE_PATH = 'http://localhost/image/images'

IMAGES_IN_SAMPLE = 5
VOLUMES_IN_SAMPLE = 2

API_VERSIONS = 'v3.2, v2.0, v1'
NUM_OF_VERSIONS = 3
IMAGE_UNVERSIONED = 'http://localhost/image'
IMAGE_VERSIONED = 'http://localhost/image/v3/'


class TestServices(testcase.TestCase):
    def setUp(self):
        super(TestServices, self).setUp()
        self.config_fixture = self.useFixture(config_fixture.Config(conf=CONF))

    def test_aggregate_key(self):
        # Aggregate 'images'
        response = json.loads(services.aggregate(IMAGES, 'images'))
        self.assertEqual(IMAGES_IN_SAMPLE, len(response['images']))

        # Aggregate 'volumes'
        response = json.loads(services.aggregate(VOLUMES, 'volumes'))
        self.assertEqual(VOLUMES_IN_SAMPLE, len(response['volumes']))

    def test_aggregate_limit(self):
        params = {
            'limit': 1
        }
        response = json.loads(services.aggregate(IMAGES, 'images',
                                                 params, IMAGE_PATH))
        self.assertEqual(1, len(response['images']))

    def test_aggregate_sort_images_ascending(self):
        """Sort images by smallest size, ascending."""
        params = {
            'sort': 'size:asc'
        }
        response = json.loads(services.aggregate(IMAGES, 'images',
                                                 params, IMAGE_PATH))
        self.assertEqual(response['images'][0]['id'], SMALLEST_IMAGE)

    def test_aggregate_sort_images_limit(self):
        """Sort images by smallest size, ascending, limit to 1, alt format."""
        params = {
            'sort_key': 'size',
            'sort_dir': 'asc',
            'limit': 1
        }
        response = json.loads(services.aggregate(IMAGES, 'images',
                                                 params, IMAGE_PATH))

        # Ensure the smallest is first and there is only 1 entry.
        self.assertEqual(response['images'][0]['id'], SMALLEST_IMAGE)
        self.assertEqual(1, len(response['images']))

        # Ensure the 'next' url is correct.
        self.assertEqual(
            Url(response['next']),
            Url(self._prepare_url(
                IMAGE_PATH,
                self._prepare_params(params, marker=SMALLEST_IMAGE)
            ))
        )

    def test_sort_images_date_limit_ascending(self):
        """Sort images by last update, ascending, limit to 2."""
        params = {
            'sort': 'updated_at:asc',
            'limit': 2
        }
        response = json.loads(services.aggregate(IMAGES, 'images',
                                                 params, IMAGE_PATH))

        # Check the first and second are the correct ids.
        self.assertEqual(response['images'][0]['id'], EARLIEST_IMAGE)
        self.assertEqual(response['images'][1]['id'], SECOND_EARLIEST_IMAGE)
        self.assertEqual(2, len(response['images']))

        # Check the next link
        self.assertEqual(
            Url(response['next']),
            Url(self._prepare_url(
                IMAGE_PATH,
                self._prepare_params(params, marker=SECOND_EARLIEST_IMAGE)
            ))
        )

    def test_sort_images_date_limit_descending(self):
        """Sort images by last update, descending, limit 1."""
        params = {
            'sort': 'updated_at:desc',
            'limit': 1
        }
        response = json.loads(services.aggregate(IMAGES, 'images',
                                                 params, IMAGE_PATH))

        # Check the id and size
        self.assertEqual(response['images'][0]['id'], LATEST_IMAGE)
        self.assertEqual(1, len(response['images']))

        # Check the next link
        self.assertEqual(
            Url(response['next']),
            Url(self._prepare_url(
                IMAGE_PATH,
                self._prepare_params(params, marker=LATEST_IMAGE)
            ))
        )

    def test_sort_images_date_ascending_pagination(self):
        """Sort images by last update, ascending, skip the first one."""
        params = {
            'sort': 'updated_at:asc',
            'limit': 1,
            'marker': EARLIEST_IMAGE
        }
        response = json.loads(services.aggregate(IMAGES, 'images',
                                                 params, IMAGE_PATH))

        # Ensure we skipped the first one
        self.assertEqual(response['images'][0]['id'], SECOND_EARLIEST_IMAGE)
        self.assertEqual(1, len(response['images']))

        # Next link
        self.assertEqual(
            Url(response['next']),
            Url(self._prepare_url(
                IMAGE_PATH,
                self._prepare_params(params, marker=SECOND_EARLIEST_IMAGE)
            ))
        )

        # Start link
        self.assertEqual(
            Url(response['start']),
            Url(self._prepare_url(
                IMAGE_PATH,
                self._prepare_params(params)
            ))
        )

    def test_marker_without_limit(self):
        """Test marker without limit."""
        params = {
            'sort': 'updated_at:asc',
            'marker': EARLIEST_IMAGE
        }

        response = json.loads(services.aggregate(IMAGES, 'images',
                                                 params, IMAGE_PATH))

        # Ensure we skipped the first one
        self.assertEqual(response['images'][0]['id'], SECOND_EARLIEST_IMAGE)
        self.assertEqual(IMAGES_IN_SAMPLE - 1, len(response['images']))

        # Start link
        self.assertEqual(
            Url(response['start']),
            Url(self._prepare_url(
                IMAGE_PATH,
                self._prepare_params(params)
            ))
        )

    def test_marker_last(self):
        """Test marker without limit, nothing to return."""
        params = {
            'sort': 'updated_at:asc',
            'marker': LATEST_IMAGE
        }

        response = json.loads(services.aggregate(IMAGES, 'images',
                                                 params, IMAGE_PATH))

        # Ensure we skipped the first one
        self.assertEqual(0, len(response['images']))

        # Start link
        self.assertEqual(
            Url(response['start']),
            Url(self._prepare_url(
                IMAGE_PATH,
                self._prepare_params(params)
            ))
        )

    def test_list_api_versions(self):

        self.config_fixture.load_raw_values(group='proxy',
                                            image_api_versions=API_VERSIONS,
                                            volume_api_versions=API_VERSIONS)

        # List image api
        response = json.loads(services.list_api_versions('image',
                                                         IMAGE_UNVERSIONED))
        current_version = response['versions'][0]['id']
        current_version_status = response['versions'][0]['status']
        current_version_url = response['versions'][0]['links'][0]['href']

        self.assertEqual(NUM_OF_VERSIONS, len(response['versions']))
        self.assertEqual(current_version, 'v3.2')
        self.assertEqual(current_version_status, 'CURRENT')
        self.assertEqual(
            Url(current_version_url),
            Url(IMAGE_VERSIONED))

    @staticmethod
    def _prepare_params(user_params, marker=None):
        params = user_params.copy()
        if marker:
            params['marker'] = marker
        else:
            params.pop('marker', None)
        return params

    @staticmethod
    def _prepare_url(url, params):
        return '%s?%s' % (url, parse.urlencode(params))
