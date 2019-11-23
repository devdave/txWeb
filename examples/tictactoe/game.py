
from enum import Enum
import typing as T
from collections import namedtuple
import random

class MapCellState(Enum):
    BLANK = 0
    PLAYER = 1
    CPU = 2

EnumerateResult = namedtuple("EnumerateResult", "index, value")
Cell = namedtuple("Cell", "pos, x, y, value")

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

    def get(self, x: int, y: T.Optional[int] = None) -> MapCellState:
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

    def enumerate(self, filter=MapCellState.BLANK) -> T.Iterator[EnumerateResult]:
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
            #  horizontals
            for step in range(self.size):
                if self.check_cells(who, list(range(self.size*step, self.size*(step+1)))) == self.size:
                    return who
            #  Verticals
            for step in range(self.size):
                if self.check_cells(who, list(range(step, self.size**2+step, self.size))) == self.size:
                    return who
            #  Diagonals
            if self.check_cells(who, [(i, i,) for i in range(self.size)]) == self.size:
                return who
            # These is a programmatic way to do this but I am too lazy/tired/blah to pull up my other implementation
            #  to see how I did it.   Probably with vectors but I don't want to do that as it's even more
            #  unreadable than the other checks
            elif self.check_cells(who, [(2, 0), (1, 1), (0, 2)]) == self.size:
                return who

        return None

    def do_cpu_move(self) -> T.Union[None, str]:
        import random

        choices = list(self.enumerate())
        index = random.choice(choices).index if choices else None
        if index is not None:
            self.set(MapCellState.CPU, index)
            index = str(index)

        return index