from autobahn.twisted.websocket import WebSocketServerFactory
from .at_wsprotocol import AtWSProtocol


class RoutedWSFactory(WebSocketServerFactory):  #pragma: no cover

    def __init__(self, url, routes, protocol_cls=AtWSProtocol, application=None):
        WebSocketServerFactory.__init__(self, url)
        self.protocol = protocol_cls

        self.routes = routes
        self._application = application

    def get_endpoint(self, name):
        return self.routes.get(name, None)


    def get_application(self):
        return self._application