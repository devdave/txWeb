"""
    Just a simple implementation of WebSocketServerFactory to provide a basic dict based router
    for server side websocket endpoints.

"""
import typing as T

from autobahn.twisted.websocket import WebSocketServerFactory
from .message_handler import MessageHandler
from .wsprotocol import WSProtocol

EndpointFunc = T.Callable[[MessageHandler], None]


class RoutedWSFactory(WebSocketServerFactory):  # pragma: no cover

    routes: T.Dict[str, T.Callable]

    def __init__(self, url, routes, protocol_cls=WSProtocol, application=None):
        WebSocketServerFactory.__init__(self, url)
        self.protocol = protocol_cls

        self.routes = routes
        self._application = application

    def get_endpoint(self, name: str) -> EndpointFunc:
        """
        Just a simple getter to return a given endpoint.

        Returns
        -------
        Returns None if the endpoint isn't in the routes dictionary.

        """
        return self.routes.get(name, None)

    def get_application(self):
        """
        Possible bad code smell but used primarily for debugging.

        """
        return self._application
