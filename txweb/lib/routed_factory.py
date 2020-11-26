from autobahn.twisted.websocket import WebSocketServerFactory
from .at_wsprotocol import AtWSProtocol

class RoutedWSFactory(WebSocketServerFactory):

    def __init__(self, url, routes, protocol_cls=AtWSProtocol, application=None):
        WebSocketServerFactory.__init__(self, url)
        self.protocol = protocol_cls

        self._application = application # Necessary so further down in protocol land we can get the session
        self.routes = routes

    def get_endpoint(self, name):
        return self.routes.get(name, None)

    def get_application(self):
        return self._application