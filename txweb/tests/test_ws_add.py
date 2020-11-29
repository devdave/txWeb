from __future__ import annotations

from unittest.mock import MagicMock

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


def test_ws_enforces_naming_conventions():

    app = WSApp(__name__)

    with pytest.raises(TypeError):
        @app.ws_add("bob", assign_args=True)
        def bad_endpoint(steve):
            pass

def test_ws_enforces_assign_args_is_kosher():

    app = WSApp(__name__)

    with pytest.raises(ValueError):
        @app.ws_add("steve", assign_args=True)
        def missing_kwargs(message, alice, bob):
            pass

def ToyConverter(arg):
    return int(arg)

def test_bad_ideas_in_code__ws_add_type_casting_via_annotations():

    app = WSApp(__name__)



    message = MessageHandler({"args": {"ich": "weis", "flag":"1", "number":"123", "other_number": "456"}}, None)

    @app.ws_add("foo", assign_args=True)
    def bar(message, ich: str = None, flag: bool = False, number: ToyConverter = None, other_number: int = None):
        return ich, flag, number, other_number,

    actual = bar(message)
    assert actual[0] == "weis"
    assert actual[1] == True
    assert actual[2] == 123
    assert actual[3] == 456