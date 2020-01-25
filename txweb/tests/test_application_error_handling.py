from twisted.web import resource as tw_resource
from twisted.web.test import requesthelper
from twisted.python.failure import Failure

import pytest
from collections import namedtuple

from unittest.mock import MagicMock
from txweb import Application
from .helper import ensureBytes, MockRequest, RequestRetval
from ..lib import StrRequest

import typing as T
from io import BytesIO
import logging




def test_basic_idea(dummy_request:RequestRetval):
    app = Application(namespace=__name__)

    dummy_request.setup(app)


    handle404 = MagicMock(return_value=False)

    app.handle_error(404)(handle404)

    dummy_request.request.requestReceived(b"GET", b"/favicon.ico", b"HTTP1/1")

    handle404.assert_called_once()
    assert dummy_request.request.finished in [True, 1]
    assert dummy_request.request.code == 404
    assert dummy_request.request.code_message == b"Resource not found"
    assert dummy_request.request is not None


def test_see_what_happens_with_bad_resources(dummy_request:RequestRetval, caplog):

    app = Application(__name__)

    dummy_request.channel.site = app.site

    @app.add("/foo")
    def handle_foo(request):
        raise RuntimeError("Where is this caught?")

    with caplog.at_level(logging.DEBUG):
        dummy_request.request.requestReceived(B"GET", b"/foo", b"HTTTP/1.1")

    assert dummy_request.request.code == 500
    assert dummy_request.read().startswith(b"HTTTP/1.1 500 Internal server error")


def test_directory_returns_404_on_missing_file(static_dir, dummy_request:RequestRetval):
    from txweb.application import Application
    app = Application(__name__)
    app.displayTracebacks = True

    directory = app.add_staticdir("/", static_dir)

    dummy_request.request.site = app.site
    dummy_request.request.requestReceived(b"GET", b"/foo.bar", b"HTTP/1.1")

    assert dummy_request.request.code == 404
    dummy_request.channel.transport.written.seek(0,0)
    content = dummy_request.channel.transport.written.read()
    debug = 1


def test_catches_and_routes_specific_exceptions(dummy_request):

    class TestException(Exception):
        pass



    app = Application(__name__)

    @app.handle_error(TestException)
    def test_handler(request:StrRequest, reason:Failure):
        request.setResponseCode(800, "Caught exception")
        request.ensureFinished()

    @app.add("/foo")
    def test_view(request):
        raise TestException("Thrown exception")


    dummy_request.request.site = app.site
    dummy_request.channel.site = app.site
    dummy_request.request.requestReceived(b"GET", b"/foo", b"HTTP/1.1")

    dummy_request.channel.transport.written.seek(0)
    test_written = dummy_request.channel.transport.written.read()

    assert dummy_request.request.code == 800
    assert dummy_request.request.code_message == b"Caught exception"

