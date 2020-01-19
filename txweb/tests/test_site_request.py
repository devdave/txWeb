from txweb.application import Application
from txweb.lib import StrRequest


def test_handles_resources_that_returns_none(dummy_request:StrRequest):

    app = Application(__name__)

    @app.add("/foo")
    def do_foo(request):
        pass


    dummy_request.request.site = app.site
    dummy_request.channel.site = app.site
    dummy_request.request.requestReceived(b"HEAD", b"/foo", b"HTTP1/1")
    debug = 1
    debug = debug + debug

