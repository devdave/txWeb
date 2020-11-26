from __future__ import annotations
import typing as T

from twisted.web.server import NOT_DONE_YET

from collections.abc import Mapping

if T.TYPE_CHECKING or False:
    # recursion import
    from .at_wsprotocol import AtWSProtocol




class MessageHandler(Mapping):

    def __init__(self, raw_message:dict, connection:AtWSProtocol):
        self.raw_message = raw_message # type: dict
        self.connection = connection

    def __getitem__(self, item):
        return self.raw_message[item]

    def __iter__(self):
        return self.raw_message.__iter__()

    def __len__(self):
        return len(self.raw_message)

    def __contains__(self, item):
        return item in self.raw_message

    def keys(self):
        return self.raw_message1.keys()

    def items(self):
        return self.raw_message.items()

    def values(self):
        return self.raw_message.values()

    def get(self, key, default=None, type=None):

        try:
            args = self['args']
            value = args[key]

        except KeyError:
            try:
                value = self[key]
            except KeyError:
                return default

        if type:
            try:
                value = type(value)
            except ValueError:
                return default

        return value

    def args(self, key, default=None, type=None):
        args = None
        value = default
        try:
            args = self['args']
        except KeyError:
            return default


        try:
            value = args[key]
        except KeyError:
            return default
        except ValueError:
            return default

        if type:
            try:
                value = type(value)
            except ValueError:
                return default

        return value

    @property
    def is_asking(self):
        return "caller_id" in self.raw_message

    def respond(self, **kwargs):
        self.connection.respondAsDict(self.raw_message, result=kwargs)
        return NOT_DONE_YET

    def tell(self, endpoint, **kwargs):
        self.connection.sendDict(endpoint=endpoint, type="tell", args=kwargs)

    def ask(self, endpoint, **kwargs):
        #TODO setup a deferred somewhere in here or below in protocol
        return self.connection.ask(endpoint, type="ask", args=kwargs)

    def get_session(self, get_key=None):
        return self.connection.application.get_session(self.connection, get_key=get_key)