from enum import Enum

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