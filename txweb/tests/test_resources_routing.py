from txweb.resources import RoutingResource

from txweb import App

import typing as T
from .helper import RequestRetval


def test_instantiates_without_error():

    class FakeSite():
        pass

    fake_site = FakeSite()

    resource = RoutingResource(fake_site)


def test_how_head_requests_are_handled(dummy_request:RequestRetval):

    app = App(__name__)

    @app.add("/foo", methods=["POST"])
    def handle_foo(request):
        return b"123"

    dummy_request.request.site = app.site
    dummy_request.channel.site = app.site
    dummy_request.request.requestReceived(b"HEAD", b"/foo", b"HTTP1/1")



