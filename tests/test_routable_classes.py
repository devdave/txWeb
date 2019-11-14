
from txweb.web_views import WebSite
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

        def hasRoutes(self, add):

            add("/number", self.respond_number)
            add("/greeting", self.render_response_says_hello)
            add("/add_one", self.adds_to_passed_get_argument)



        def respond_number(self, request):
            return 1234

        def render_response_says_hello(self, request):
            return "Hello"


        def adds_to_passed_get_argument(self, request):
            """
                subviews do not need to start with render_
            """
            input = int(request.args[b'number'][0])

            return input + 1

    number_request = MockRequest("/nexus/number")
    number_resource = app.getResourceFor(number_request)

    debug = 123


def test_throws_exception_on_inaccessible_view_class():


    app = WebSite()

    with pytest.raises(UnrenderableException):
        @app.add("/base")
        class Foo:
            pass

