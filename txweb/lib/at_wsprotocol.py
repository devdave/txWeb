try:
    import ujson as json
except ImportError:
    import json

from uuid import uuid4
import warnings


from twisted.web.server import NOT_DONE_YET
from twisted.internet.defer import Deferred

from autobahn.twisted.websocket import WebSocketServerProtocol

from .message_handler import MessageHandler

from txweb.log import getLogger

class AtWSProtocol(WebSocketServerProtocol):

    my_log = getLogger()
    """
        To prevent an OOM/out of memory event, limit the number of 
        pending asks to 100
    """
    MAX_ASKS = 100  # Need to make this tunable

    def __init__(self, *args, **kwargs):
        self.pending_responses = {}

        super(AtWSProtocol, self).__init__(*args, **kwargs)
        # WebSocketServerProtocol.__init__(self, *args, **kwargs)

        self.identity = None
        self.on_disconnect = Deferred()
        # for tracking deferred `ask` calls
        self.deferred_asks = {}


        # self._raw_message = {}

    # @property
    # def application(self):
    #     return self.factory.get_application()

    def getCookie(self, cookie_name, default=None):
        raw_cookies = self.http_headers.get('cookie', "")
        cookies = {}
        for params in raw_cookies.split(";"):
            str_name, value = params.split("=")
            if str_name.strip() == cookie_name:
                return value.strip()

        return default

    def onConnect(self, request):
        self.identity = uuid4().hex
        self.my_log.debug("Client connecting: {request.peer}", request=request)

    def onClose(self, wasClean, code, reason):
        self.on_disconnect.addErrback(self.my_log.error)
        self.on_disconnect.callback(self.identity)
        del self.on_disconnect
        self.my_log.debug("WebSocket connection closed: {reason!r}", reason=reason)

    def sendDict(self, **values):
        response = json.dumps(values)
        # Always send synchronously for now
        self.sendMessage(response.encode("utf-8"), isBinary=False, sync=True)

    def respond(self, original_message, result):
        self.sendDict(caller_id=original_message['caller_id'], result=result)

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
            requestToken = uuid4().hex
            d = Deferred()
            self.deferred_asks[requestToken] = d
            self.sendDict(endpoint=endpoint, type="ask", caller_id=requestToken, args=values)
            return d
        else:
            raise EnvironmentError("Maximum # of pending asks reached")

    def onMessage(self, payload, isBinary):
        if isBinary:
            return None # I don't know how to deal with binary

        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError:
            warnings.warn(f"Failed to decode {payload}")
            return

        try:
            raw_message = json.loads(payload)
        except json.JSONDecodeError:
            warnings.warn(f"Corrupt/bad payload: {payload}")
            return

        message = MessageHandler(raw_message, self)
        result = None

        if message.get("type") == "response":
            caller_id = message.get("caller_id", None)

            if caller_id is not None and caller_id in self.deferred_asks:
                d = self.deferred_asks[caller_id] # type: Deferred
                d.callback(message.get("result"))
                del self.deferred_asks[caller_id]
            else:
                warnings.warn(f"Response to ask {caller_id} arrived but was not found in deferred_asks")

        elif "endpoint" in message:
            endpoint_func = self.factory.get_endpoint(message['endpoint'])
            # self.my_log.debug("Processing {endpoint_func!r}", endpoint_func=endpoint_func)

            if endpoint_func is None:
                self.my_log.error("Bad endpoint {endpoint}", endpoint=call_data['endpoint'])
                return
            else:
                result = endpoint_func(message)
        else:
            self.my_log.error("Got message without an endpoint or caller_id: {raw!r}", raw=message.raw_message)
            # raise Exception("Got message without a endpoint")

        if result in [NOT_DONE_YET, None]:
            return
        elif isinstance(result, Deferred):
            return
        elif "type" in message and message['type'] == "ask":
            self.respondAsDict(message, result=result)
        else:
            warnings.warn(f"{endpoint_func} returned {result} but I don't know know how to handle it.")
            pass


