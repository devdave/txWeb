from txweb.lib.message_handler import MessageHandler


def test_type_casting():

    message = MessageHandler({"foo":"1"}, None)
    actual = message.get("foo", vtype=int)
    assert actual == 1


def test_type_casting_args():
    message = MessageHandler({"args": {"foo":"1"}}, None)
    actual = message.args("foo", vtype=int)
    assert actual == 1