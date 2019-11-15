
from enum import Enum
import sys
import json

from txweb.web_views import WebSite

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

    def __init__(self):
        self.users = {}

    def announce(self, msg_type, message, username):
        for user in self.users.values():
            user(msg_type, message, username)

    def getUsername(self, request):
        session = request.getSession(IDictSession)
        username = session.get("username", None)
        if username is None:
            raise ValueError("Username not set")

        return username

    def setUsername(self, request, username):
        session = request.getSession(IDictSession)
        session['username'] = username

    def onUserLogoff(self, username):
        """
        For whatever reason, username has logged off
        """
        self.users.pop(username, None)
        self.announce(EventTypes.USER_LEFT, f"{username} has logged out")


    @Site.expose("/register", methods=["POST"])
    def register(self, request:server.Request):
        response = request.json
        self.setUsername(request, response['username'])
        username = self.getUsername(request)
        return json.dumps(dict(result="OK",username=repr(username)))


    @Site.expose("/logoff")
    def logoff(self, request:server.Request):
        username = self.getUsername(request)

        if username in self.users:
            del self.users[username]

        return json.dumps(dict(result="OK", username=repr(username)))


    @Site.expose("/tell", methods=["POST"])
    def tell(self, request):
        response = request.json
        msg_type = EventTypes(response['type'])
        try:
            username = self.getUsername(request)
        except ValueError:
            #TODO use log
            print("Unable to find username for request")
            return json.dumps(dict(result="ERROR", reason="Unable to post message as username is not set!"))
        else:
            self.announce(msg_type, response['message'], username)
            return json.dumps(dict(result="OK"))

    @Site.expose("/listen")
    def listen(self, request:server.Request):
        username = self.getUsername(request)

        def write_response(msg_type: EventTypes, message: str, username: str = None):
            data = json.dumps(dict(type=msg_type.value, message=message, username=username))
            print("Sending: ", data)
            request.write(f"data: {data}\n\n".encode("utf-8"))


        def on_event(msg_type: EventTypes, message: str, username=None):
            write_response(msg_type, message, username)


        def on_close(error):
            self.deregister(username)
            # assume connection is closed

        request.setHeader("Cache-control", "no-cache")
        request.setHeader("Content-Type", "text/event-stream")

        write_response(EventTypes.USER_JOINED, f"Welcome {username!r} joined", "server");
        self.announce(EventTypes.USER_JOINED, f"{username!r} joined chat", "server")

        self.users[username] = on_event

        return NOT_DONE_YET



def main():
    print("Main called, starting reactor")
    log.startLogging(sys.stdout)
    reactor.listenTCP(8123, Site)
    reactor.run()


if __name__ == "__main__":
    main()

