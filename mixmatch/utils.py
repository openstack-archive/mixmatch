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

import uuid


class CachedProperty(object):
    """A decorator that converts a function into a lazy property.

    Taken from : https://github.com/nshah/python-memoize
    The function wrapped is called the first time to retrieve the result
    and then that calculated result is used the next time you access
    the value:

        class Foo(object):

            @CachedProperty
            def bar(self):
                # calculate something important here
                return 42

    """

    def __init__(self, func, name=None, doc=None):
        self.func = func
        self.__name__ = name or func.__name__
        self.__doc__ = doc or func.__doc__

    def __get__(self, obj, owner):
        if obj is None:
            return self
        value = self.func(obj)
        setattr(obj, self.__name__, value)
        return value


def safe_get(a, i, default=None):
    """Return the i-th element if it exists, or default."""
    try:
        return a[i]
    except IndexError:
        return default


def safe_pop(a, i=0, default=None):
    """Pops the i-th element, if any, otherwise returns default"""
    try:
        return a.pop(i)
    except (IndexError, KeyError):
        return default


def is_uuid(value):
    """Return true if value is a valid uuid."""
    try:
        uuid.UUID(value, version=4)
        return True
    except (ValueError, TypeError):
        return False


def pop_if_uuid(a, index=None):
    """Pops the first or index element of the list only if it is a uuid."""
    if index:
        if is_uuid(safe_get(a, index)):
            return safe_pop(a, i=index)
        else:
            return None
    else:
        if is_uuid(safe_get(a, 0)):
            return safe_pop(a)
        else:
            return None


def flatten(item):
    """Return the first element if list-like, otherwise the item itself"""
    if isinstance(item, list):
        return item[0]
    return item
