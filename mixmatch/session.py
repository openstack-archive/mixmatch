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


import flask
from keystonemiddleware import auth_token as ksm
from keystonemiddleware.auth_token import _request
import webob

FEDOPS_PATH = "/fedops"

app = flask.Flask(__name__)
request = flask.request

mm_proxy = flask.Blueprint("proxy", __name__)
mm_api = flask.Blueprint("api", __name__)


def __get_app(*args, **kwargs):
    """Dummy function only for use with Paste."""
    return app


class _SelectiveKeystoneMiddleware(ksm.AuthProtocol):
    @webob.dec.wsgify(RequestClass=_request._AuthTokenRequest)
    def __call__(self, req):
        path = req.environ['PATH_INFO']
        if path.startswith(FEDOPS_PATH):
            super(_SelectiveKeystoneMiddleware, self).__call__(req)
        return self._app


def ksm_filter_factory(global_conf, **local_conf):
    """Like the original filter_factory from ksm, but with special class."""
    conf = global_conf.copy()
    conf.update(local_conf)

    def auth_filter(app):
        return _SelectiveKeystoneMiddleware(app, conf)
    return auth_filter


def chunked_reader():
    try:
        # If we're running under uWSGI, use the uwsgi.chunked_read method
        # to read chunked input.
        import uwsgi  # noqa

        while True:
            chunk = uwsgi.chunked_read()
            if len(chunk) > 0:
                yield chunk
            else:
                return
    except ImportError:
        # Otherwise try to read the wsgi input. This works in embedded Apache.
        stream = flask.request.environ["wsgi.input"]
        try:
            while True:
                yield stream.next()
        except Exception:
            return
