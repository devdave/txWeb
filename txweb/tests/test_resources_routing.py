from unittest.mock import MagicMock

from twisted.web.resource import NoResource

from txweb.resources import RoutingResource
from txweb import App
from txweb.http_codes import Unrenderable
from txweb.resources import ViewClassResource

from unittest.mock import sentinel
import typing as T

from .helper import RequestRetval

import pytest


def test_instantiates_without_error():

    class FakeSite:
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
    dummy_request.request.requestReceived(b"HEAD", b"/foo", b"HTTP/1.1")
    assert dummy_request.request.code == 405
    assert dummy_request.request.code_message == b"Method not allowed"



def test_ensure_blows_up_with_a_bad_add():

    app = App(__name__)
    bad_asset = sentinel


    with pytest.raises(ValueError) as excinfo:
        app.add("/trash")(bad_asset)

        assert "expected callable|Object|twisted.web.resource.Resource" in str(excinfo.value)


def test_ensure_blowsup_with_a_class_that_has_no_way_to_render():

    app = App(__name__)

    with pytest.raises(Unrenderable):
        @app.add("/trash")
        class BaseClass(object):
            pass

def test_ensure_a_classic_like_class_is_routed():


    app = App(__name__)


    @app.add("/trash")
    class GoodClass(object):

        def render(self, request):
            return b"Rendered"

    first_key = next(iter(app.router.iter_rules()))
    endpoint = app.router._endpoints[first_key.endpoint]
    assert isinstance(endpoint, ViewClassResource)
    debug = 1

def test_ensure_resource_is_added():

    app = App(__name__)

    app.add_resource("/404", resource=NoResource())

    first_key = next(iter(app.router.iter_rules()))
    endpoint = app.router._endpoints[first_key.endpoint]
    assert isinstance(endpoint, NoResource)
    debug = 1


def test_handle_add_slashes(dummy_request:RequestRetval):

    app = App(__name__)

    mock = MagicMock()

    app.route("/js/")(mock)

    dummy_request.request.site = app.site
    dummy_request.channel.site = app.site
    dummy_request.request.requestReceived(b"GET", b"/js", b"HTTP/1.1")

    assert dummy_request.request.code == 308
    assert dummy_request.request.code_message == b"Permanent Redirect"
    assert dummy_request.request.responseHeaders.getRawHeaders(b"location") == [b"http://10.0.0.1/js/"]
    assert mock.call_count == 0




