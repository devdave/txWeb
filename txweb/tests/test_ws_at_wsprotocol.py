from unittest.mock import MagicMock
from dataclasses import dataclass

from twisted.internet.defer import inlineCallbacks

from txweb.lib.wsprotocol import WSProtocol

@dataclass(frozen=True)
class CapturedMessage:
    payload: str
    isBinary: bool
    fragmentSize:int
    sync:bool
    doNotCompress:bool

class MockFactory:
    def __init__(self, endpoints):
        self.endpoints = endpoints

    def get_endpoint(self, endpoint):
        return self.endpoints[endpoint]

class TrackingProtocol(WSProtocol):

        def __init__(self, *args, **kwargs):
            super(TrackingProtocol, self).__init__(*args, **kwargs)
            self.messages = []
            self.http_headers = {}


        def sendMessage(self,
                    payload,
                    isBinary=False,
                    fragmentSize=None,
                    sync=False,
                    doNotCompress=False):
            self.messages.append(CapturedMessage(payload, isBinary, fragmentSize, sync, doNotCompress))

def mock_protocol(endpoints):
    factory = MockFactory(endpoints)
    protocol = TrackingProtocol()
    protocol.factory = factory
    return protocol, factory

def mock_message(**kwargs):
    from json import dumps
    raw = dumps(kwargs)
    return raw.encode("utf-8")



def test_imports():
    pass # catch syntax errors and cyclical imports


def test_instantiates():
    mock_func = MagicMock()
    protocol, factory = mock_protocol({"foo": mock_func})

def test_getCookie():
    protocol, factory = mock_protocol({})

    protocol.http_headers['cookie'] = "foo=bar; blah=123; thing=creature"


    assert protocol.getCookie("foo") == "bar"
    assert protocol.getCookie("blah") == "123"
    assert protocol.getCookie("thing") == "creature"

    dud = protocol.getCookie("doesn't exist", default=None)
    assert dud is None


def test_open_and_closed_deferred_works():

    protocol, factoryt = mock_protocol({})

    assert protocol.identity is None

    protocol.onConnect(None)

    actual_id = protocol.identity
    track_call = MagicMock()

    protocol.on_disconnect.addCallback(track_call)

    protocol.onClose(True, 200, None)

    track_call.assert_called_once_with(actual_id)


def test_onMessage():
    import json

    mock_func = MagicMock()
    mock_func.return_value = None
    protocol, factory = mock_protocol(dict(endpoint1=mock_func))

    payload = dict(endpoint="endpoint1", type="tell")
    dumped = json.dumps(payload).encode("utf-8")

    protocol.onMessage(dumped, False)

    mock_func.assert_called_once()


def test_deferred_ask():

    import json

    @inlineCallbacks
    def asking_func(message):

        result = yield message.ask("remote.add", first=1, second=2)
        message.tell("result_was", logic=result)
        assert result == 4

    protocol, factory = mock_protocol({"test_endpoint": asking_func})
    protocol.onMessage(mock_message(type="call", endpoint="test_endpoint"), False)
    captured = protocol.messages[0] # type: CapturedMessage
    ask_msg = json.loads(captured.payload)

    assert ask_msg['type'] == "ask"
    assert len(protocol.deferred_asks) == 1

    caller_id = ask_msg['caller_id']

    protocol.onMessage(mock_message(type="response", caller_id=caller_id, result=4), False)

    assert len(protocol.messages) == 2

    latest = protocol.messages[-1] # type: CapturedMessage
    tell_msg = json.loads(latest.payload)

    assert tell_msg['type'] == "tell"
    assert tell_msg['args']['logic'] == 4

