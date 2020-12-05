"""
    A wrapper around the message sent from the client

    Breaks ideal style guides as it also wraps around the connection object to make
    responding and interacting with the client easier.

"""
from __future__ import annotations
import typing as T
from collections.abc import Mapping

# from twisted.web.server import NOT_DONE_YET


if T.TYPE_CHECKING or False:  # pragma: no cover
    # recursion import
    from .wsprotocol import WSProtocol


class MessageHandler(Mapping):  # pragma: no cover

    raw_message: T.Dict[T.AnyStr, T.Any]
    connection: WSProtocol

    def __init__(self, raw_message: dict, connection: WSProtocol):
        self.raw_message = raw_message  # type: dict
        self.connection = connection

    def __getitem__(self, item):  # pragma: no cover
        return self.raw_message[item]

    def __iter__(self):  # pragma: no cover
        return self.raw_message.__iter__()

    def __len__(self):  # pragma: no cover
        return len(self.raw_message)

    def __contains__(self, item):  # pragma: no cover
        return item in self.raw_message

    def keys(self):  # pragma: no cover
        return self.raw_message.keys()

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

    @property
    def identity(self):
        """
            Utility to make it quicker to access the connection's unique identifier
        :return:
        """
        return self.connection.identity

    # pylint: disable=redefined-builtin
    def args(self, key, default=None, type=None):
        """
            A more explicit/direct getter that looks for an `args` dictionary in the client message and
            if it exists, returns the requested key.
        :param key:
        :param default:
        :param type:  What type to cast the arg value as.  (eg type=int would cast a str to int if possible)
        :return:
        """

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
        """
            If the message was an request/ask for response, send back a result.
        :param result:
        :return:
        """
        return self.connection.respond(self.raw_message, result=result)

    def tell(self, endpoint, **kwargs):
        """
        Tell the client to do something if it provides the requested end point.
        :param endpoint:
        :param kwargs:
        :return:
        """
        return self.connection.tell(endpoint, **kwargs)

    def ask(self, endpoint, **kwargs):
        """
            Ask the client for information or acknowledgement of success/failure for an action.
        :param endpoint:
        :param kwargs:
        :return:
        """
        return self.connection.ask(endpoint, type="ask", args=kwargs)

    def get_session(self, get_key=None):
        """
            see WSProtocol's get_session
        :param get_key:
        :return:
        """
        return self.connection.application.get_session(self.connection, get_key=get_key)
