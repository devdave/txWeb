
from .helper import MagicMock, RequestRetval

from txweb import Application


def test_basic_concept(dummy_request:RequestRetval):

    app = Application()

    before_mock = MagicMock()
    after_mock = MagicMock()
    fake_url_handler = MagicMock(return_value=b"Empty")

    before_mock = app.before_render(before_mock)
    after_mock = app.after_render(after_mock)
    app.add("/foo")(fake_url_handler)

    dummy_request.request._call_after_render = app._call_after_render
    dummy_request.request._call_before_render = app._call_before_render
    dummy_request.request.channel.site = app.site
    dummy_request.request.site = app.site

    dummy_request.request.requestReceived(b"GET", b"/foo", b"HTTP1/1")


    before_mock.assert_called_once()
    after_mock.assert_called_once()


