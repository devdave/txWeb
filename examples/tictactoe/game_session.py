from zope.interface import Interface, Attribute, implementer
from twisted.web import server
from zope.interface import Interface, Attribute, implementer
from twisted.python.components import registerAdapter

from game import Game


class IGameSession(Interface):
    game = Attribute("Hold a copy of the Tic-tac-toe Game container")

@implementer(IGameSession)
class GameSession(object):
    """
        To make testing easier, the GameSession only holds a reference to the actual
        game logic
    """
    def __init__(self, session):
        self.game = Game()

registerAdapter(GameSession, server.Session, IGameSession)