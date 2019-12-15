
import pytest

from twisted.web.resource import NoResource

from txweb.web_views import WebSite
from txweb.errors import UnrenderableException
from .helper import MockRequest

def test_basic_idea():

    app = WebSite()

    @app.add("/nexus")
    class PersistentObject(object):

        def __init__(self):
            self._number = 0


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

        @app.expose("/counter")
        def increments_persistant_value(self, request):
            self._number += 1
            return self._number


    assert len(app.resource._route_map._rules) == 4

    number_request = MockRequest([], "/nexus/number")
    number_resource = app.getResourceFor(number_request)

    assert isinstance(number_resource, NoResource) is False
    expected = b"1234"
    actual = number_resource.render(number_request)
    assert actual == expected

    add_request = MockRequest([], "/nexus/add_one", {b"number":5})
    resource = app.getResourceFor(add_request)
    expected = b"6"
    actual = resource.render(add_request)
    assert actual == expected

    incrementer = MockRequest([], "/nexus/counter")
    assert app.getResourceFor(incrementer).render(incrementer) == 1 #This is a bug because NOT_DONE_YET =='s 1
    assert app.getResourceFor(incrementer).render(incrementer) == b"2"
    assert app.getResourceFor(incrementer).render(incrementer) == b"3"




def test_throws_exception_on_inaccessible_view_class():


    app = WebSite()

    with pytest.raises(UnrenderableException):
        @app.add("/base")
        class Foo:
            pass






