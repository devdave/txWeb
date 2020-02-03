
from txweb.resources import ViewClassResource
from .helper import MockRequest
from unittest.mock import sentinel


def test_basic():

    sentinel_string = "foo_boo_1234"

    class StubView():

        def render_POST(self, request):
            return sentinel_string

    resource = ViewClassResource(None, StubView())
    request = MockRequest([],"/")
    request.method = B"POST"

    actual = resource.render(request)

    assert actual == sentinel_string.encode("utf-8")


def test_post_filter():

    sentinel_string = "Foo_1234_blah"

    class StubView():

        def render(self,request):
            return "Doesn't matter"

        def post_filter(self, request, output):
            assert output == "Doesn't matter"
            return sentinel_string


    resource = ViewClassResource(None, StubView())
    request = MockRequest([], "/")

    actual = resource.render(request)
    assert actual == sentinel_string.encode("utf-8")


def test_pre_filter():

    class Stub():

        def prefilter(self, request, view_resource):
            request.args['was_set'] = True

        def render(self, request):
            assert request.args['was_set'] is True
            return b""


    resource = ViewClassResource(None, Stub())
    request = MockRequest([], "/")
    resource.render(request)