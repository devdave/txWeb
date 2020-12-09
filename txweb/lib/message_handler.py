"""
    A wrapper around the message sent from the client

    Breaks ideal style guides as it also wraps around the connection object to make
    responding and interacting with the client easier.

"""
from __future__ import annotations
import typing as T
from collections.abc import Mapping

from twisted.internet.defer import Deferred


if T.TYPE_CHECKING or False:  # pragma: no cover
    # pylint: disable=cyclic-import
    # used for type hinting with PyCharm but this would break the app if it was ever imported.
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

    # pylint: disable=redefined-builtin
    def get(self, key: str, default=None, vtype: type=None):
        """

        Parameters
        ----------
        key
        default
        vtype

        Returns
        -------

        """



        try:
            value = self[key]
        except KeyError:
            return default

        if vtype:
            try:
                value = vtype(value)
            except ValueError:
                return default

        return value

    @property
    def identity(self) -> str:
        """
            Utility to make it quicker to access the connection's unique identifier

        Returns
        -------
        A unique identifier string

        """
        return self.connection.identity

    # pylint: disable=redefined-builtin
    def args(self, key: str, default=None, vtype=None):
        """
            A more explicit/direct getter that looks for an `args` dictionary in the client message and
            if it exists, returns the requested key.

        Parameters
        ----------
        key: str
            A dict key for the message's `args` subdictionary of arguments

        default: str
            TODO implement a not empty default sentinel.

        vtype: type
            Used to cast the requested key's value into.  (eg vtype=int would cast key=foo to int or try to atleast)

        Returns
        -------
            T.Any
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

        if vtype:
            try:
                value = vtype(value)
            except ValueError:
                return default

        return value

    def respond(self, result) -> None:
        """
        For client messages that are `ask` type, send back a response to their request.

        Parameters
        ----------
        result: T.Any
            Anything that can be serialized by json.dumps is a valid variable type.

        Returns
        -------
        None

        """
        return self.connection.respond(self.raw_message, result=result)

    def tell(self, endpoint: str, **kwargs) -> None:
        """
        Tell the client to do something at the specified `endpoint`

        Parameters
        ----------
        endpoint: str
            Ideally a valid client side endpoint
        kwargs: dict
            json serializable friendly data

        Returns
        -------
        None
        """
        return self.connection.tell(endpoint, **kwargs)

    def ask(self, endpoint: str, **kwargs: T.Dict[str, T.Any]) -> Deferred:
        """
            Ask the client for information or acknowledgement of success/failure for an action.

            Parameters
            ----------
            endpoint
            kwargs

            Returns
            -------
            A Deferred object the server side code can add a callback to.
        """
        return self.connection.ask(endpoint, type="ask", args=kwargs)

    def get_session(self, get_key: str=None) -> T.Union[T.Dict, T.Any]:
        """
            See WSProtocol's get_session

        Parameters
        ----------
        get_key: str
            A shortcut to fetch a specific key of the session dictionary versus grabbing the whole dictionary.

        Returns
        -------

        """
        return self.connection.application.get_session(self.connection, get_key=get_key)
