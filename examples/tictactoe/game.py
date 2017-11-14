import attr
import random

class Error(BaseException):
    def __init__(self, issue):
        super().__init__(issue)

        self.rule_error = issue


class State(object):
    EMPTY = 0
    P1 = 1
    CPU = 2

@attr.s
class Rules(object):

    map = attr.ib()
    
    def check(self):

        forwardslash = [0, 4 , 8]
        backslash = [2, 4, 6]
        players = [State.P1, State.CPU]

        #horz's
        for y in range(0, 3):
            row = [self.map.get(x,y) for x in range(0, 3)]
            for player in players:
                if all([cell == player for cell in row]):
                    return player

        #Verticals now
        for x in range(0, 3):
            row = [self.map.get(x,y) for y in range(0, 3)]
            for player in players:
                if all([cell == player for cell in row]):
                    return player

        #diagonals


        if self.map.get(1,1) != State.EMPTY:
            for test in [forwardslash, backslash]:
                row = [self.map.iget(pos) for pos in test]

                for player in players:
                    if all([cell == player for cell in row]):
                        return player

        return False

    def move(self, where, who = State.P1):

        game_state = self.check()

        if game_state != False:
            raise Error(f"{game_state} already won.")

        if self.map.iget(where) != State.EMPTY:
            raise Error(f"Position {self.i2c(position)} already set to {repr(self.data[position])}, must be {repr(GameMap.EMPTY)}")

        self.map.iset(where, who)

        game_state = self.check()

        if game_state != False:
            raise Error(f"{game_state} has won.")
            
        #Idiot AI time
        options = self.map.filter(State.EMPTY)
        if len(options) == 0:
            raise Error("No more moves, stalemate")
            
        next_move = random.choice(options)
        self.map.iset(next_move, State.CPU)

        game_state = self.check()
        if game_state != False:
            raise Error(f"{game_state} has won.")






@attr.s
class Map:
    """

    for i in range(0,9):  print(i, i%3, i//3)
    0:0,0 1:1,0 2:2,0
    3:0,1 4:1,1 5:2,1
    6:0,2 7:1,2 8:2,2

    """


    data = attr.ib()


    def i2c(self, position):

        x = position % 3
        y = position // 3

        return (x+step, y+step,)

    def iget(self, position):
        return self.data[position]

    def get(self, x,y):
        return self.iget((y*3)+x)

    def iset(self, position, value):
        self.data[position] = value

    def set(self, x, y, value):
        self.iset((y*3)+x, value)


    def filter(self, match):
        return [pos for pos, value in enumerate(self.data, 0) if value == match]

    def raw(self):
        return "".join([str(i) for i in self.data])


def Factory(raw_input):


    if raw_input in [None, "None"]:
        print("new map")
        new_state = [0 for i in range(0,9)]
    elif isinstance(raw_input, bytes):
        new_state = [int(i) for i in raw_input.decode()]
    elif isinstance(raw_input, str):
        new_state = [int(i) for i in raw_input]

    game_map = Map(data=new_state)

    return Rules(game_map)



