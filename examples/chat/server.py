
from enum import Enum
import sys
import json
import typing as T

from txweb.web_views import WebSite, StrRequest

from zope.interface import Interface, Attribute, implementer
from twisted.python.components import registerAdapter

from twisted.web.static import File
from twisted.web import server
from twisted.internet import reactor, defer
from twisted.web.server import NOT_DONE_YET
from twisted.python import log


class NoValue:
    pass

class IDictSession(Interface):
    _data = Attribute("A dictionary where key is a str and value is a primitive type")

@implementer(IDictSession)
class DictSession(object):
    def __init__(self, session):
        self._data = {}

    def __setitem__(self, key, value):
        self._data[key] = value

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=NoValue):
        if default is NoValue:
            return self[key]
        else:
            return self._data.get(key, default)

    def __contains__(self, key):
        return key in self._data

registerAdapter(DictSession, server.Session, IDictSession)


Site = WebSite()
Site.add_resource("/", File("./index.html"))
Site.add_resource("/index.js", File("./script.js", defaultType="text/javascript"))

class EventTypes(Enum):
    USER_SAYS = 1
    USER_JOINED = 2
    USER_LEFT = 3
    CONNECTION_CLOSED = 4

@Site.add("/messageboard")
class MessageBoard(object):
    """
    Provides a web message board via the connections: register, logoff, tell, and listen


    """

    def __init__(self):
        self.users = {} # type: T.Dict[str, T.Set[T.Callable, StrRequest]]


    def _add_user(self, username: str, callback:T.Callable, request:StrRequest):
        if username in self.users:
            raise ValueError(f"{username} is already registered")

        self.users[username] = (callback, request,)

    def _remove_user(self, username: str):
        self.users.pop(username, None)

    def _check_users(self):
        """
        TODO add StrRequest.onConnectionTimeout and or StrRequest.onConnectionClosed methods

        Watches the registered users for disconnections and connection timeouts
        """
        for username, (write_event, request) in self.users.items(): # type: T.AnyStr, T.Callable, StrRequest
            #TODO figure out how to know if connection is closed
            pass


    def _announce(self, msg_type: EventTypes, message:str, username:str):
        """
        Iterates over connected users and relays either a user message or
        a server side event.
        """
        for (write_event, connection) in self.users.values():
            write_event(msg_type, message, username)

    def _get_username(self, request):
        session = request.getSession(IDictSession)
        username = session.get("username", None)
        if username is None:
            raise ValueError("Username not set")

        return username

    def _set_username(self, request, username):
        if username in self.users:
            raise ValueError(f"{username} is already registered")

        session = request.getSession(IDictSession)
        session['username'] = username

    def _on_user_logoff(self, username):
        """
        For whatever reason, username has logged off
        """
        self.users.pop(username, None)
        self.announce(EventTypes.USER_LEFT, f"{username} has logged out")


    @Site.expose("/register", methods=["POST"])
    def register(self, request:server.Request):
        response = request.json
        try:
            self._set_username(request, response['username'])
        except ValueError as e:
            return json.dumps(dict(result="ERROR", reason= repr(e.args)))

        username = self._get_username(request)
        return json.dumps(dict(result="OK",username=repr(username)))


    @Site.expose("/logoff")
    def logoff(self, request:server.Request):
        username = self._get_username(request)

        self._remove_user(username)

        return json.dumps(dict(result="OK", username=repr(username)))


    @Site.expose("/tell", methods=["POST"])
    def tell(self, request):
        response = request.json
        msg_type = EventTypes(response['type'])
        try:
            username = self._get_username(request)
        except ValueError:
            #TODO use log
            print("Unable to find username for request")
            return json.dumps(dict(result="ERROR", reason="Unable to post message as username is not set!"))
        else:
            self._announce(msg_type, response['message'], username)
            return json.dumps(dict(result="OK"))

    @Site.expose("/listen")
    def listen(self, request:server.Request):

        def write_response(msg_type: EventTypes, message: str, username: str = None):
            data = json.dumps(dict(type=msg_type.value, message=message, username=username))
            print("Sending: ", data)
            request.write(f"data: {data}\n\n".encode("utf-8"))


        def on_event(msg_type: EventTypes, message: str, username=None):
            write_response(msg_type, message, username)


        def on_close(reason):
            print("Handling connection closed")
            print(repr(reason))
            username = "Unknown"

            try:
                username = self._get_username(request)
                self._remove_user(username)
            except ValueError as e:
                #Do nothing
                print("Got Exception")
                print(repr(e))
                pass
            else:
                self._announce(EventTypes.USER_LEFT, f"{username!r}  left", "server")
            # assume connection is closed

            return True

        # Setup Server Side Event headers
        request.setHeader("Cache-control", "no-cache")
        request.setHeader("Content-Type", "text/event-stream")

        request.notifyFinish().addErrback(on_close)



        try:
            username = self._get_username(request)
        except ValueError:
            write_response(EventTypes.CONNECTION_CLOSED, "Username not set", "server")
            request.finish()
            return NOT_DONE_YET
        else:

            write_response(EventTypes.USER_JOINED, f"Welcome {username!r}", "server");
            self._announce(EventTypes.USER_JOINED, f"{username!r} joined chat", "server")
            self._add_user(username, on_event, request)

            return NOT_DONE_YET



def main():
    print("Main called, starting reactor")
    log.startLogging(sys.stdout)
    reactor.listenTCP(8123, Site)
    reactor.run()


if __name__ == "__main__":
    main()

