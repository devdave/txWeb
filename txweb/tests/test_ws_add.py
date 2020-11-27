import pytest
from txweb.lib.message_handler import MessageHandler
from txweb import Application as WSApp


def test_ws_add_works():

    app = WSApp(__name__) # type: WSApp

    @app.ws_add("foo.bar")
    def provide_foo_bar(message):
        pass

    assert "foo.bar" in app.ws_endpoints

def test_ws_assign_args_flag_works():

    app = WSApp(__name__)

    @app.ws_add("alice.bob", assign_args=True)
    def provide_alice_bob(message, which_one: str = None):
        return which_one

    message = MessageHandler(dict(args=dict(which_one="Steve!!!")), None)

    result = provide_alice_bob(message)

    assert result == "Steve!!!"