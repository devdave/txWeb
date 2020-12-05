from pathlib import Path
from dataclasses import dataclass
import sys

from twisted.internet import reactor
from twisted.python.log import startLogging

from txweb import Texas
from txweb.lib.message_handler import MessageHandler
from txweb.lib.wsprotocol import WSProtocol
from txweb.util.reloader import reloader

HERE = Path(__file__).parent


app = Texas(__name__)


# Serve home.html from http://{HOST}:{PORT}/
app.add_file("/", HERE / "home.html")
app.add_file("/chat.js", HERE / "chat.js")

@dataclass(frozen=True)
class User:
    name: str
    identity: str
    emitter: WSProtocol


@app.ws_class
class Chat:

    def __init__(self, application: Texas):
        self.app = application
        self.users = {}

    def on_user_leave(self, identity):

        if identity in self.users:
            user = self.users[identity]
            print(f"{user}@{identity} has disconnected")
            del self.users[identity]

            self.emit("SERVER", f"{user.name} has disconnected")

    def emit(self, who, what):
        print(f"Emitting to {len(self.users)} users")
        for identity, user in self.users.items():
            user: User  # No magic here, just a typehint
            user.emitter.tell("client.hear", who=who, what=what)


    @app.ws_expose(assign_args=True)
    def register(self, message:MessageHandler, username:str = None):
        """

        :param message:
        :param username:
        :return:
        """
        print(f"New registration: {username} @ {message.identity}")

        self.users[message.identity] = User(username, message.identity, message.connection)
        message.connection.on_disconnect.addCallback(self.on_user_leave)
        self.emit("SERVER", f"{username} has joined.")

        return True

    @app.ws_expose(assign_args=True)
    def speak(self, message: MessageHandler, text:str = None):
        user = self.users[message.connection.identity]
        print(f"New chat: {user.name}@{message.identity} says {text!r}")
        self.emit(user.name, text)



def main():
    HOST = "127.0.0.1"
    PORT = 7070

    # provide a websocket connection at ws://{HOST}:{POST}/ws for the client side
    app.enable_websockets(f"ws://{HOST}:{PORT}", "/ws")
    app.ws_sharelib("/lib")
    app.listenTCP(PORT, HOST)
    print(f"Listening on http://{HOST}:{PORT}/")
    reactor.run()


if __name__ == "__main__":
    startLogging(sys.stdout)
    reloader(main)