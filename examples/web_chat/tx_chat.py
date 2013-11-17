from txweb import Site, expose
from twisted.internet import reactor, defer
from twisted.web.server import NOT_DONE_YET

from txzmq import ZmqEndpoint, ZmqFactory, ZmqPubConnection, ZmqSubConnection

class ZeHub(object):

    def __init__(self):
        self.zf = ZmqFactory()
        self.bind_to = "tcp://127.0.0.1:5555"
        self.server = ZmqEndpoint('bind', self.bind_to)
        self.client = ZmqEndpoint('connect', self.bind_to)
        self.server_s = ZmqPubConnection(self.zf, self.server)
        self.clients = []

    def send(self, msg):
        self.server_s.publish(msg)

    def on_msg(self, callBack, time_out = None):


        print "Waiting for msg"


        client = ZmqSubConnection(self.zf, self.client)
        client.subscribe("")
        self.clients.append(client)
        print self.clients

        def cleanup():
            print client
            c_index = self.clients.index(client)
            self.clients.pop(c_index)
            client.shutdown()

        def on_msg(*args, **kwargs):
            print args
            try:
                callBack(args)
            finally:
                cleanup()





        client.gotMessage = on_msg






import time

class WebRoot(object):

    def __init__(self, hub):
        self.hub = hub

    @expose
    def index(self, request):
        return "Hello world! %s" % time.time()

    @expose
    def say(self, request):
        ts = time.time()
        msg = "said %s" % ts
        self.hub.send(msg)
        return msg

    @expose
    def hear(self, request):

        def on_event(msg):
            request.write(str(msg))
            request.finish()

        self.hub.on_msg(on_event)
        from dbgp.client import brk; brk("192.168.1.2", 9090)
        return NOT_DONE_YET


def run():
    reactor.listenTCP(8080, Site(WebRoot(ZeHub())))
    reactor.run()

if __name__ == '__main__':
    run()