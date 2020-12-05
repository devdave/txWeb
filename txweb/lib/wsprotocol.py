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

    my_log = getLogger()
    """
        To prevent an OOM/out of memory event, limit the number of 
        pending asks to 100
    """
    MAX_ASKS = 100  # Need to make this tunable
    factory: RoutedFactory

    def __init__(self):
        self.pending_responses = {}

        super().__init__()
        # WebSocketServerProtocol.__init__(self, *args, **kwargs)

        self.identity = None
        self.on_disconnect = Deferred()
        # for tracking deferred `ask` calls
        self.deferred_asks = {}

    @property
    def application(self):
        """
            Utility intended mostly for unit-testing
        :return:
        """
        return self.factory.get_application()

    def getCookie(self, cookie_name, default=None):
        """
            Mirror's the behavior of StrRequest.getCookie

        :param cookie_name:
        :param default:
        :return:
        """
        raw_cookies = self.http_headers.get('cookie', "")
        for params in raw_cookies.split(";"):
            str_name, value = params.split("=")
            if str_name.strip() == cookie_name:
                return value.strip()

        return default

    def onConnect(self, request):
        """
            Set's a unique identifier for the connection.


        :param request:
        :return:
        """
        self.identity = uuid4().hex
        self.my_log.debug("Client connecting: {request.peer}", request=request)

    def onClose(self, was_clean, code, reason):
        """
            Connection was lost, currently I don't care why but I likely should.
        :param was_clean:
        :param code:
        :param reason:
        :return:
        """
        self.on_disconnect.addErrback(self.my_log.error)
        self.on_disconnect.callback(self.identity)
        del self.on_disconnect
        self.my_log.debug("WebSocket connection closed: {reason!r}", reason=reason)

    def sendDict(self, **values):
        """
            Utility used by every other method that follows
        :param values:
        :return:
        """
        response = json.dumps(values)
        # Always send synchronously for now
        self.sendMessage(response.encode("utf-8"), isBinary=False, sync=True)

    def respond(self, original_message, result):
        """
            The client asked for a result/response.

        :param original_message:
        :param result:
        :return:
        """
        self.sendDict(caller_id=original_message['caller_id'], type="response", result=result)

    def tell(self, endpoint, **values):
        """
            Tell the client to do something and don't expect a response

        :param endpoint:
        :param values:
        :return:
        """
        self.sendDict(endpoint=endpoint, type="tell", args=values)

    def ask(self, endpoint, **values):
        """
            Ask the client to do something and I should get a response back.

        :param endpoint:
        :param values:
        :return:
        """
        if len(self.deferred_asks) < self.MAX_ASKS:
            request_token = uuid4().hex
            d = Deferred()
            self.deferred_asks[request_token] = d
            self.sendDict(endpoint=endpoint, type="ask", caller_id=request_token, args=values)
            return d
        else:
            raise EnvironmentError("Maximum # of pending asks reached")

    def handleResponse(self, message):
        """
            Server side asked client a question, shunt this message through the
             deferred_asks collection of deferreds to the appropriate/waiting endpoint

        :param message:
        :return:
        """
        caller_id = message.get("caller_id", None)

        if caller_id is not None and caller_id in self.deferred_asks:
            d = self.deferred_asks[caller_id]  # type: Deferred
            d.callback(message.get("result"))
            del self.deferred_asks[caller_id]
        else:
            warnings.warn(f"Response to ask {caller_id} arrived but was not found in deferred_asks")

    def handleEndPoint(self, message):
        """
            Handles incoming ask and tell messages.

        :param message:
        :return:
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



    def onMessage(self, payload, is_binary):
        """
            Entry point for incoming messages from the client

        :param payload:
        :param is_binary:
        :return:
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



