from enum import Enum
from collections import namedtuple
import typing as T
import json
import sys

from txweb.web_views import WebSite
from txweb.util.str_request import StrRequest

from twisted.internet import reactor
from twisted.python import log
from twisted.web import server
from twisted.web.static import File
from zope.interface import Interface, Attribute, implementer
from twisted.python.components import registerAdapter

from game import Game, MapCellState, Cell

"""
    The Enums are intended to avoid typo's between client and server 
    as there are matching constant's on the client side.
    
"""
class ActionTypes(Enum):
    RESET = "RESET"
    MOVE = "MOVE"

class ResponseTypes(Enum):
    OK = "OK"
    ERROR = "ERROR"
    WIN = "WIN"
    STALEMATE = "STALEMATE"
    RESET = "RESET"
    MOVE = "MOVE"

    # Details
    PLAYER = "player"
    CPU = "cpu"
    WTF = "WTF"



class IGameSession(Interface):
    game = Attribute("A simple list that defaults to len of nine 0's")

@implementer(IGameSession)
class GameSession(object):
    """
        To make testing easier, the GameSession only holds a reference to the actual
        game logic
    """
    def __init__(self, session):
        self.game = Game()

registerAdapter(GameSession, server.Session, IGameSession)






class RequestArgs(object):
    __slots__ = ("command", "detail")

    def __init__(self, request: StrRequest):
        data = request.json
        self.command = data.get("command", "RESET")
        self.detail = data.get("detail", None)

    def __repr__(self):
        return f"<RequestArgs command={self.command} detail={self.detail}>"




class ResponseData:
    def __init__(self, status, state, detail):
        self.status = status.value if isinstance(status, ResponseTypes) else status
        self.state = state.value if isinstance(state, ResponseTypes) else state
        self.detail = detail

    def _asdict(self):
        return dict(status=self.status, state=self.state, detail=self.detail)

    @property
    def json(self):
        return json.dumps(self._asdict())



"""
The actual webserver logic
==========================

That's a lot of cruft for a simple T3 game but I've written this game so many times
that I've just found it easier to over engineer as it cuts down on bugs.

"""

Site = WebSite()

index = Site.add_file("/", "./index.html", defaultType="text/html")
scriptjs = Site.add_file("/script.js", "./script.js", defaultType="text/javascript")



@Site.add("/do", methods=["POST"])
def handle_do(request: StrRequest) -> bytes:
    """
        Expects JSON {"command": str, "detail": int or str}
        responds with {"status": str, "state": str, "detail": str or int }

        Checks to see if the game is being reset and if not it records the player move
        and then makes the cpu move.

    """

    game = request.getSession(IGameSession).game # type: Game
    order = RequestArgs(request)

    request.setHeader("Content-Type", "application/json")

    if order.command == ActionTypes.RESET.value:
        game.clear()
        response = ResponseData(ResponseTypes.RESET, ResponseTypes.OK, "")

    # Player is making their move
    elif order.command == ActionTypes.MOVE.value:
        # make sure they're not trying to take an occupied cell
        if game.get(int(order.detail)) != MapCellState.BLANK:
            response = ResponseData(ResponseTypes.ERROR, ResponseTypes.MOVE, order.detail)
        else:
            # Cell is empty, set it to be owned by the Player
            game.set(MapCellState.PLAYER, int(order.detail))

            #Check for player won
            if game.check_winner() == MapCellState.PLAYER:
                response = ResponseData(ResponseTypes.WIN, ResponseTypes.PLAYER, order.detail)

            #Check if the player created a stale mate
            elif game.matching_count(MapCellState.BLANK) == 0:
                response = ResponseData(ResponseTypes.STALEMATE, ResponseTypes.PLAYER, order.detail)
            else:

                # Now it's the CPU's turn
                move = game.do_cpu_move()

                # Did the CPU win?
                if game.check_winner() == MapCellState.CPU:
                    response = ResponseData(ResponseTypes.WIN, ResponseTypes.CPU, move)

                # Did they use the last free cell?
                elif game.matching_count(MapCellState.BLANK) == 0:
                    response = ResponseData(ResponseTypes.STALEMATE, ResponseTypes.CPU, move)

                # They didn't win and there isn't a stalemate
                else:
                    response = ResponseData(ResponseTypes.MOVE, ResponseTypes.CPU, move)

    return response.json.encode("utf-8")



def main():
    print("Main called, starting reactor")
    log.startLogging(sys.stdout)
    reactor.listenTCP(8123, Site)
    reactor.run()


if __name__ == "__main__":
    main()