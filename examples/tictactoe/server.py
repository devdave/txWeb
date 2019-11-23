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

class MapCellState(Enum):
    BLANK = 0
    PLAYER = 1
    CPU = 2


Cell = namedtuple("Cell", "pos, x, y, value")


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

class Game():
    """
    I have written tic tac toe for every language and framework I've ever used
    so I've gotten it somewhat streamlined

    Given a grid like
        Y   0   1   2
    X   --------------
    0   |   0   1   2|
    1   |   3   4   5|
    2   |   6   7   8|
        -------------
    it can be stored like this
    [012345678] (versus, [(0,0),(0,1),(0,2)...] )

    and then XY coords can be converted to list index position

    Damn if I remember what this math is called but
        list index position can be found by multiplying x by # of columns plus Y
        geometric coords can be found by index modula # of columns and then subtracting the multiple of x to get y

    examples
    column_height = 3
    (1,1) = (x * column_height + y) = 4
    0 = (0,0)
    1 = (1 % column_height = 0, 1-(x*column_height) = 1) = (0,1)
    4 = (4 % column_height = 1, 4-(x*column_height) = 1) = (1,1)
    7 = (7 % column_height = 2, 7-(x*column_height) = 1) = (2,1)

    This works for all grids where the maximum of X and Y are equal.
    """

    def __init__(self):
        self.size = 3
        self.map = [MapCellState.BLANK for _ in range(self.size**2)]

    def set(self, state: MapCellState, x: int, y: T.Optional[int] = None):
        index = (x*self.size) + y if y is not None else x
        self.map[index] = state

    def set_list(self, state: MapCellState, cells: T.List[T.Union[T.Tuple[int, int], int]] ):
        for cell in cells:
            if isinstance(cell, tuple):
                self.set(state, cell[0], cell[0])
            elif isinstance(cell, int):
                self.set(state, cell)
            else:
                raise ValueError(f"{type(cell)}-{cell!r}")

    def get(self, x: int, y: T.Optional[int] = None):
        return self.map[x] if y is None else self.map[(x*self.size)+y]

    def get_list(self, cells: T.Union[T.List[int], T.List[T.Tuple[int, int]]]) -> T.List[MapCellState]:
        collect = []
        for cell in cells:
            if isinstance(cell, tuple):
                retval = self.get(cell[0], cell[1])
            elif isinstance(cell, int):
                retval = self.get(cell)

            collect.append(retval)

        return collect

    def enumerate(self, filter=MapCellState.BLANK):
        EnumerateResult = namedtuple("EnumerateResult", "index, value")
        for index, value in enumerate(self.map):
            if value == filter:
                yield EnumerateResult(index, value)

    def clear(self):
        self.map = [MapCellState.BLANK for _ in range(self.size**2)]

    def __iter__(self):
        for index, state in enumerate(self.map):
            x = index // self.size
            y = index-(x*self.size)
            yield Cell(index, x, y, state)

    def matching_count(self, value: MapCellState) -> int:
        return sum([1 for cell in self.map if cell == value ])

    def check_cells(self, value, cells):
        count = 0
        for cell in cells:
            if isinstance(cell, tuple):
                x, y = cell
            else:
                x, y = (cell, None,)

            if self.get(x, y) == value:
                count += 1

        return count


    def check_winner(self):
        # Brute force this as I am drunk and can't remember the easy way
        for who in [MapCellState.PLAYER, MapCellState.CPU]:
            #horizontals
            for step in range(self.size):
                if self.check_cells(who, list(range(self.size*step, self.size*(step+1)))) == self.size:
                    return who
            #Vertiicals
            for step in range(self.size):
                if self.check_cells(who, list(range(step, self.size**2+step, self.size))) == self.size:
                    return who
            #Diagonals
            if self.check_cells(who, [(i,i,) for i in range(self.size)]) == self.size:
                return who
            # These is a programmatic way to do this but I am too lazy/tired/blah to pull up my other implementation
            #  to see how I did it.   Probably with vectors but I don't want to do that as it's even more
            #  unreadable than the other checks
            elif self.check_cells(who, [(2,0),(1,1),(0,2)]) == self.size:
                return who

        return None




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

def do_cpu_move(map: Game) -> T.Union[None, str]:
    import random
    choices = list(map.enumerate())
    index = random.choice(choices).index if choices else None
    if index is not None:
        map.set(MapCellState.CPU, index)
        index = str(index)

    return index

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

    map = request.getSession(IGameSession).game # type: GameSession
    order = RequestArgs(request)

    request.setHeader("Content-Type", "application/json")

    if order.command == ActionTypes.RESET.value:
        map.clear()
        response = ResponseData(ResponseTypes.RESET, ResponseTypes.OK, "")

    # Player is making their move
    elif order.command == ActionTypes.MOVE.value:
        # make sure they're not trying to take an occupied cell
        if map.get(int(order.detail)) != MapCellState.BLANK:
            response = ResponseData(ResponseTypes.ERROR, ResponseTypes.MOVE, order.detail)
        else:
            # Cell is empty, set it to be owned by the Player
            map.set(MapCellState.PLAYER, int(order.detail))

            #Check for player won
            if map.check_winner() == MapCellState.PLAYER:
                response = ResponseData(ResponseTypes.WIN, ResponseTypes.PLAYER, order.detail)

            #Check if the player created a stale mate
            elif map.matching_count(MapCellState.BLANK) == 0:
                response = ResponseData(ResponseTypes.STALEMATE, ResponseTypes.PLAYER, order.detail)
            else:

                # Now it's the CPU's turn
                move = do_cpu_move(map)

                # Did the CPU win?
                if map.check_winner() == MapCellState.CPU:
                    response = ResponseData(ResponseTypes.WIN, ResponseTypes.CPU, move)

                # Did they use the last free cell?
                elif map.matching_count(MapCellState.BLANK) == 0:
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