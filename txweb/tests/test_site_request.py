import pytest

from txweb.application import Application
from txweb.lib import StrRequest
from .conftest import RequestRetval


def test_handles_resources_that_returns_none(dummy_request:RequestRetval):

    app = Application(__name__)

    @app.add("/foo")
    def do_foo(request):
        pass


    dummy_request.request.site = app.site
    dummy_request.channel.site = app.site

    with pytest.raises(RuntimeError):
        dummy_request.request.requestReceived(b"HEAD", b"/foo", b"HTTP1/1")

    assert dummy_request.request.code == 500
    assert dummy_request.request.code_message == b'Internal server error'

