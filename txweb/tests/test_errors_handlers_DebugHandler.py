
from txweb import Application
from txweb.lib.errors.handler import DebugHandler
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
        raise Exception()

    dummy_request.request.requestReceived(b"GET", b"/foo", b"HTTP/1.1")

    dummy_request.request.content.seek(0,0)
    content = dummy_request.request.content.read()

    assert len(content) > 0
    assert dummy_request.request.code == 500
    assert dummy_request.request.code_message == b"Internal server error"




