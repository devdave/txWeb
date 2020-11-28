from __future__ import annotations
import typing as T

from twisted.web.server import NOT_DONE_YET

from collections.abc import Mapping

if T.TYPE_CHECKING or False: # pragma: no cover
    # recursion import
    from .at_wsprotocol import AtWSProtocol




class MessageHandler(Mapping): #pragma: no cover

    raw_message: T.Dict[T.str, T.Any]
    connection: AtWSProtocol

    def __init__(self, raw_message:dict, connection:AtWSProtocol):
        self.raw_message = raw_message # type: dict
        self.connection = connection

    def __getitem__(self, item):  # pragma: no cover
        return self.raw_message[item]

    def __iter__(self):  # pragma: no cover
        return self.raw_message.__iter__()

    def __len__(self):  # pragma: no cover
        return len(self.raw_message)

    def __contains__(self, item): # pragma: no cover
        return item in self.raw_message

    def keys(self):  # pragma: no cover
        return self.raw_message1.keys()

    def items(self):  # pragma: no cover
        return self.raw_message.items()

    def values(self):  # pragma: no cover
        return self.raw_message.values()

    def get(self, key, default=None, type=None):

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

    def respond(self, result):
        return self.connection.respond(self.raw_message, result=result)

    def tell(self, endpoint, **kwargs):
        return self.connection.tell(endpoint, **kwargs)

    def ask(self, endpoint, **kwargs):
        return self.connection.ask(endpoint, type="ask", args=kwargs)

    def get_session(self, get_key=None):
        return self.connection.application.get_session(self.connection, get_key=get_key)