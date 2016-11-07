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

app = flask.Flask(__name__)
request = flask.request


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
        except:
            return
