import json

from server import Game, MapCellState, IGameSession, handle_do
from twisted.web.test.requesthelper import DummyRequest

class MockRequest(DummyRequest):

    def getSession(self, component=None):
        session = DummyRequest.getSession(self)
        if component is not None:
            return session.getComponent(component)
        else:
            return session

    def setJSON(self, data):
        self.json = data


def test_game_count():

    map = Game()

    assert map.matching_count(MapCellState.BLANK) == 9


def test_game_set():

    map = Game()

    map.set(MapCellState.CPU, 4)
    assert map.map[4] == MapCellState.CPU

    map.set(MapCellState.PLAYER, 1, 1)
    assert map.map[4] == MapCellState.PLAYER

def test_game_get():

    map = Game()
    map.map[6] = MapCellState.CPU
    assert map.get(2,0) == MapCellState.CPU

def test_game_map_size():
    map = Game()
    assert len(map.map) == 9


def test_game_check_winner():
    map = Game()
    assert map.check_winner() is None

    map.clear()
    map.set_list(MapCellState.CPU, [6, 4, 2])
    assert map.check_winner() == MapCellState.CPU

    map.clear()
    map.set_list(MapCellState.PLAYER, [(2, 0,), (1, 1,), (0, 2,)])
    assert map.check_winner() == MapCellState.PLAYER

    map.clear()
    map.set_list(MapCellState.PLAYER, [0, 4, 8])
    assert map.check_winner() == MapCellState.PLAYER

def test_check_for_stalemate():

    map = Game()

    map.set_list(MapCellState.PLAYER, [1, 3, 4, 8])
    map.set_list(MapCellState.CPU, [0, 2, 5, 6, 7])
    assert map.matching_count(MapCellState.BLANK) == 0
    assert map.check_winner() is None


def test_first_move():

    request = MockRequest([])
    request.setJSON(dict(command="MOVE", detail="4"))

    raw_response = handle_do(request)
    # This is tough because the CPU picks something as random
    response = json.loads(raw_response)
    assert response['status'] == "MOVE"
    assert response['state'] == "cpu"
    cpu_move = int(response['detail'])

    map = request.session.getComponent(IGameSession).game
    assert map.get(cpu_move) == MapCellState.CPU
    assert map.get(4) == MapCellState.PLAYER


def test_enumerate_works():

    map = Game()
    map.set_list(MapCellState.PLAYER, [0,1,2,3,4,5,6,7])

    choices = list(map.enumerate())
    assert len(choices) == 1
    assert choices[0].value == MapCellState.BLANK
