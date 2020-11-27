from unittest.mock import MagicMock
from dataclasses import dataclass

from txweb.lib.at_wsprotocol import AtWSProtocol

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

class TrackingProtocol(AtWSProtocol):

        def __init__(self, *args, **kwargs):
            super(TrackingProtocol, self).__init__(*args, **kwargs)
            self.messages = []


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



def test_imports():
    pass # catch syntax errors and cyclical imports


def test_instantiates():
    mock_func = MagicMock()
    protocol, factory = mock_protocol({"foo": mock_func})




