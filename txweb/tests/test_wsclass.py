import pytest

from txweb import Application as WSApp
from txweb.lib.message_handler import MessageHandler

def test_concept():

    app = WSApp(__name__)


    @app.ws_class
    class Dummy(object):

        def __init__(self, application: WSApp):
            self.app = application

        @app.ws_expose
        def hello(self, connection, message):
            return "World"

        @app.ws_expose
        def sum_nums(self, connection, message):
            return sum(message.get('arguments', []))


    assert "dummy.hello" in app.ws_endpoints
    assert "dummy.sum_nums" in app.ws_endpoints


def test_persistence():

    app = WSApp(__name__)

    @app.ws_class
    class Dummy2(object):

        def __init__(self, app: WSApp):
            self.app = app
            self.counter = 0

        @app.ws_expose
        def increment(self, connection, message):
            self.counter += 1
            return None


    assert app.ws_instances['dummy2'].counter == 0
    app.ws_endpoints['dummy2.increment'](None, {})
    assert app.ws_instances['dummy2'].counter == 1


def test_magic_arguments():
    app = WSApp(__name__)


    @app.ws_class
    class Endpoint:

        def __init__(self, app):
            self.app = app

        @app.ws_expose(assign_args=True)
        def test_function(self, message, foo=False, bar=None):
            return foo, bar

        with pytest.raises(TypeError, match="^ws_expose convention expects.*"):

            @app.ws_expose(assign_args=True)
            def test_bad_convention(self, protocol, incoming):
                pass

    assert "endpoint" in app.ws_instances

    instance = app.ws_instances['endpoint']

    message = MessageHandler({"args":dict(foo=True, bar="Hello World!")}, None)

    foo, bar = instance.test_function(message)

    assert foo == True
    assert bar == "Hello World!"

    assert hasattr(instance.test_function, app.WS_EXPOSED_FUNC) is True

