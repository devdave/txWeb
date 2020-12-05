import pytest

from unittest.mock import MagicMock

from txweb import Application
from txweb.lib.errors import DebugHandler
from txweb.lib.str_request import StrRequest

from .helper import MockRequest
from .helper import RequestRetval

def test_handler_doesnt_blowup():

    app = Application(__name__)  # type: Application

    handler = DebugHandler(app)
    app.add_error_handler(handler, "default", override=True)


def test_handler_catches_error(dummy_request:RequestRetval):

    app = Application(__name__)
    dummy_request.request.site = app.site
    dummy_request.channel.site = app.site

    @app.add("/foo")
    def handle_foo(request):
        raise RuntimeError()

    with pytest.raises(RuntimeError):
        dummy_request.request.requestReceived(b"GET", b"/foo", b"HTTP/1.1")

    dummy_request.request.transport.written.seek(0,0)
    content = dummy_request.request.transport.written.read()

    assert len(content) > 0
    assert dummy_request.request.code == 500
    assert dummy_request.request.code_message == b"Internal server error"

def test_handler_catches_resources_that_return_none(dummy_request:RequestRetval):
    app = Application(__name__)
    dummy_request.request.site = app.site
    dummy_request.channel.site = app.site

    @app.add("/foo")
    def handle_foo(request):
        pass

    with pytest.raises(RuntimeError):
        dummy_request.request.requestReceived(b"GET", b"/foo", b"HTTP/1.1")

    dummy_request.request.transport.written.seek(0, 0)
    content = dummy_request.request.transport.written.read()

    assert len(content) > 0
    assert dummy_request.request.code == 500
    assert dummy_request.request.code_message == b"Internal server error"


def test_error_custom_errorhandler(dummy_request: RequestRetval):

    app = Application(__name__)
    dummy_request.site = app.site
    fake_handler = MagicMock(return_val = True)

    class TestError(Exception):
        pass

    @app.add("/throws")
    def throws_error(request):
        raise TestError()

    app.handle_error(TestError)(fake_handler)

    #  unlike the default handler, this swallows the exception
    dummy_request.request.requestReceived(b"GET", b"/throws", b"HTTP/1.1")

    # assert we caught this correctly
    fake_handler.assert_called()



def test_error_custom_errorhandler_prevents_duplicates(dummy_request: RequestRetval):

    app = Application(__name__)
    dummy_request.site = app.site
    fake_handler = MagicMock(return_val = True)

    class TestError(Exception):
        pass

    app.handle_error(TestError)(fake_handler)
    with pytest.raises(ValueError):
        app.handle_error(TestError)(fake_handler)











