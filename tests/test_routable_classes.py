
import pytest

from twisted.web.resource import NoResource

from txweb.web_views import WebSite, UnrenderableException
from .helper import MockRequest

def test_basic_idea():

    app = WebSite()

    @app.add("/nexus")
    class PersistentObject(object):

        def __init__(self):
            self._site = None

        def needsSite(self, site):
            self._site = site

        @property
        def site(self):
            return self._site


        @app.expose("/number")
        def respond_number(self, request):
            return 1234

        @app.expose("/greeting")
        def render_response_says_hello(self, request):
            return "Hello"


        @app.expose("/add_one")
        def adds_to_passed_get_argument(self, request):
            """
                subviews do not need to start with render_
            """
            input = int(request.args[b'number'][0])

            return input + 1

    assert len(app.resource._route_map._rules) == 3

    number_request = MockRequest("/nexus/number")
    number_resource = app.getResourceFor(number_request)

    assert isinstance(number_resource, NoResource) is False

    debug = 123


def test_throws_exception_on_inaccessible_view_class():


    app = WebSite()

    with pytest.raises(UnrenderableException):
        @app.add("/base")
        class Foo:
            pass






