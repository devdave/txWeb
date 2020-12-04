from autobahn.twisted.websocket import WebSocketServerFactory
from .wsprotocol import WSProtocol


class RoutedWSFactory(WebSocketServerFactory):  #pragma: no cover

    def __init__(self, url, routes, protocol_cls=WSProtocol, application=None):
        WebSocketServerFactory.__init__(self, url)
        self.protocol = protocol_cls

        self.routes = routes
        self._application = application

    def get_endpoint(self, name):
        return self.routes.get(name, None)


    def get_application(self):
        return self._application