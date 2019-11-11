import time

from txweb import Site, expose
from twisted.web.static import File
from twisted.internet import reactor, defer
from twisted.web.server import NOT_DONE_YET

from txzmq import ZmqEndpoint, ZmqFactory, ZmqPubConnection, ZmqSubConnection

class ZeHub(object):
    """
        Actual business logic of this example:

        Hub opens a central server publisher socket
            and then on demand builds client sockets
    """

    def __init__(self):
        self.zf = ZmqFactory()
        self.bind_to = "tcp://127.0.0.1:5555"
        #These are just a namedtuples that hold the connection type AND
        # the target address.
        self.server = ZmqEndpoint('bind', self.bind_to)
        self.client = ZmqEndpoint('connect', self.bind_to)
        #The actual publisher/server socket
        self.server_s = ZmqPubConnection(self.zf, self.server)
        #A brute force way to hold client sockets and prevent them from
        # getting lost.
        self.clients = []

    def send(self, msg):
        """
            Publishes a message onto the pub/sub
            :param msg: Expected to be a simple string message
        """
        self.server_s.publish(msg)

    def on_msg(self, callBack, time_out = None):
        """
            A messy callback handler for when a new message pops up.
            :param callBack: expected def callBack(stringMessage)
            :param time_out: TODO a timeout value in seconds
        """

        """
            This is a tad not production sane as its going to open a new ZMQ
            socket for every single message sent.  Its fine when it's just 1-2
            people chatting for a short-demo duration but a better approach might
            be to bind the client ZMQ socket to a HTTP session with a timeout.

            So say someone leaves, the HTTP session would timeout after some T duration
            and this socket would be cleaned up.  Additionally this would prevent
            some amount of thrash of instantiating and destroying sockets.
        """
        client = ZmqSubConnection(self.zf, self.client)
        client.subscribe("")
        self.clients.append(client)
        print(len(self.clients), " waiting clients")

        def cleanup():
            """
                Our message is done, clean up!
            """
            c_index = self.clients.index(client)
            self.clients.pop(c_index)
            client.shutdown()


        def on_msg(*args, **kwargs):
            try:
                callBack("".join(args[:-1]))
            finally:
                cleanup()

        """
            Blink and you might miss it, this does the actual binding
            to the client socket.

            Initially I thought "Man this would be some much better using a deferred"
            EXCEPT what happens after that first deferred fires?
        """
        client.gotMessage = on_msg




class WebRoot(object):

    def __init__(self, hub):
        self.hub = hub

    index = File("./index.html")

    @expose
    def say(self, request):
        ts = time.time()
        msg = "%s: %s" %( ts, request.args.get("msg", ["..."])[0])
        self.hub.send(msg)
        return msg

    @expose
    def hear(self, request):

        def on_event(msg):
            request.write(str(msg))
            request.finish()

        self.hub.on_msg(on_event)
        return NOT_DONE_YET


def run():
    reactor.listenTCP(8080, Site(WebRoot(ZeHub())))
    reactor.run()

if __name__ == '__main__':
    run()
