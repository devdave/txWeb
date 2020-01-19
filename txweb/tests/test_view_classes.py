
from txweb.application import Application

def test_correctly_adds_classes_to_routing_map():

    app = Application(__name__)

    @app.add_class("/foo")
    class Foo(object):

        @app.expose("/hello")
        def hello(self, request):
            return b"World"

    assert len(app.router._route_map._rules) == 1
    assert app.router._route_map._rules[0].rule == "/foo/hello"
