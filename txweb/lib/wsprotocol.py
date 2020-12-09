"""
    Bridge/interface between the client and server.

    Provides a deferred to notify interested listeners if the connection closes.
    Provides ask, tell, and respond helpers that match the same verbage/methods on the javascript ResilientSocket class.


"""
from __future__ import annotations
try:
    import ujson as json
except ImportError:
    import json

import typing as T
from uuid import uuid4
import warnings


from twisted.web.server import NOT_DONE_YET
from twisted.internet.defer import Deferred

from autobahn.twisted.websocket import WebSocketServerProtocol

from txweb.log import getLogger

from .message_handler import MessageHandler




class WSProtocol(WebSocketServerProtocol):
    """
        Handles new websocket connections by routing them to the requested endpoint.

        All incoming requests from the client match one of two JSON formats

        1. The message has an `endpoint` key and `type` set to either "ask" or "tell"
            If type is set to ask, a caller_id key MUST be present so the response can be properly routed back.

        2. The message has a `type` key set to "response"


        Attributes
        ----------
        my_log: Logger
        MAX_ASKS: int
            The maximum number of pending asks to wait for from the client
        factory:
            Reference to the factory which spawned this protocol/connection
        identity: str
            A unique identifier for this connection which MUST be different than what is used for cookies
        on_disconnect: Deferred
            A deferred to allow for parts of the server application to be notified when the connection closes
        deferred_asks: T.Dict[str, Deferred]
            All pending deferred asks to the client.


    """
    my_log = getLogger()
    MAX_ASKS = 100  # Need to make this tunable
    factory: RoutedFactory

    def __init__(self):
        self.pending_responses = {}

        super().__init__()

        self.identity = None
        self.on_disconnect = Deferred()
        # for tracking deferred `ask` calls
        self.deferred_asks = {}

    @property
    def application(self):
        """
            Utility intended mostly for unit-testing

        Returns
        -------
        The current instance of Texas

        """
        return self.factory.get_application()

    def getCookie(self, cookie_name: str, default=None) -> str:
        """
            Mirror's the behavior of StrRequest.getCookie

        Parameters
        ----------
        cookie_name: str
        default: str

        Returns
        -------
        If the cookie exists, it returnx the cookie value ELSE returns `default` which is set to None by default
        """
        raw_cookies = self.http_headers.get('cookie', "")
        for params in raw_cookies.split(";"):
            str_name, value = params.split("=")
            if str_name.strip() == cookie_name:
                return value.strip()

        return default

    def onConnect(self, request) -> T.NoReturn:
        """
            Hook to the underlying websocket protocol so a unique identifier for the connection can be set.
            Called externally by the protocol factory class.


        """
        self.identity = uuid4().hex
        self.my_log.debug("Client connecting: {request.peer}", request=request)

    def onClose(self, was_clean: bool, code: int, reason) -> T.NoReturn:
        """
            Connection was lost, currently I don't care why but I likely should.

        Parameters
        ----------

        was_clean: bool
        code: int
        reason: unknown

        """
        self.on_disconnect.addErrback(self.my_log.error)
        self.on_disconnect.callback(self.identity)
        # Delete the Deferred to force it to be garbage collected and emit any unhandled errors as soon as possible
        del self.on_disconnect
        self.my_log.debug("WebSocket connection closed: {reason!r}", reason=reason)

    def sendDict(self, **values) -> T.NoReturn:
        """
            Utility used by every other method that follows

        Raises
        ------
        TypeError
            Throws this if a key/value in values cannot be encoded to JSON (eg. Enum)

        Parameters:
        -----------
        values: dict
            A valid dictionary view of arguments that can be serialized by JSON

        """
        response = json.dumps(values)
        # Always send synchronously for now
        self.sendMessage(response.encode("utf-8"), isBinary=False, sync=True)

    def respond(self, original_message, result) -> T.NoReturn:
        """
            The client asked for a result/response.

        Parameters
        ----------
        original_message: MessageHandler or dict
            The original request message so caller_id can be retrieved



        """
        self.sendDict(caller_id=original_message['caller_id'], type="response", result=result)

    def tell(self, endpoint: str, **values) -> T.NoReturn:
        """
            Tell the client to do something and don't expect a response

        Parameters
        ----------
        endpoint: str
            The remote client side endpoint to be told to do something.

        """
        self.sendDict(endpoint=endpoint, type="tell", args=values)

    def ask(self, endpoint, **values) -> Deferred:
        """
            Ask the client to do something and I should get a response back.

            Creates a Deferred object so the server side application can be notified of a response

        Parameters
        ----------
        endpoint: str
        values: dict
            dictionary of keyname arguments to be serialized and sent to the client.


        """
        if len(self.deferred_asks) < self.MAX_ASKS:
            request_token = uuid4().hex
            d = Deferred()
            self.deferred_asks[request_token] = d
            self.sendDict(endpoint=endpoint, type="ask", caller_id=request_token, args=values)
            return d
        else:
            raise EnvironmentError("Maximum # of pending asks reached")

    def handleResponse(self, message: MessageHandler) -> T.NoReturn:
        """
            Server side asked client a question, shunt this message through the
             deferred_asks collection of deferreds to the appropriate/waiting endpoint

        Parameters
        ----------
        message: MessageHandler
            The client request with the response to a server ask

        """
        caller_id = message.get("caller_id", None)

        if caller_id is not None and caller_id in self.deferred_asks:
            d = self.deferred_asks[caller_id]  # type: Deferred
            d.callback(message.get("result"))
            del self.deferred_asks[caller_id]
        else:
            warnings.warn(f"Response to ask {caller_id} arrived but was not found in deferred_asks")

    def handleEndPoint(self, message: MessageHandler) -> T.NoReturn:
        """
            Handles incoming ask and tell messages.

        :param message:

        """
        endpoint_func = self.factory.get_endpoint(message['endpoint'])
        self.my_log.debug("Processing {endpoint!r}", endpoint=message['endpoint'])

        if endpoint_func is None:
            self.my_log.error("Bad endpoint {endpoint}", endpoint=message['endpoint'])
        else:
            result = endpoint_func(message)

            if result in [NOT_DONE_YET, None]:
                return
            elif isinstance(result, Deferred):
                return
            elif message.get("type", default=None) == "ask":
                self.respond(message, result=result)
            else:
                warnings.warn(f"{endpoint_func} returned {result} but I don't know know how to handle it.")



    def onMessage(self, payload, is_binary) -> T.NoReturn:
        """
            Entry point for incoming messages from the client

        :param payload:
        :param is_binary:

        """

        if is_binary:  # pragma: no cover
            warnings.warn("Received binary payload, don't know how to deal with this.")
            return

        try:  # pragma: no cover
            payload = payload.decode("utf-8")
            raw_message = json.loads(payload)
        except UnicodeDecodeError:  # pragma: no cover
            warnings.warn(f"Failed to decode {payload}")
        except json.JSONDecodeError:  # pragma: no cover
            warnings.warn(f"Corrupt/bad payload: {payload}")
        else:

            message = MessageHandler(raw_message, self)

            if message.get("type") == "response":
                self.handleResponse(message)
            elif "endpoint" in message:
                self.handleEndPoint(message)
            else:
                self.my_log.error("Got message without an endpoint or caller_id: {raw!r}", raw=message.raw_message)



