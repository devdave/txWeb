
from twisted.web import resource
from twisted.internet import defer
from twisted.web.server import NOT_DONE_YET



def get_thing_name(thing: object) -> str:
    """
        Attempts to return a unique and informative name for thing

        Currently relies exclusively on __qualname__ as per https://www.python.org/dev/peps/pep-3155/

    """

    return getattr(thing, "__qualname__") #throws exception if it doesn't have __qualname__ property


