import inspect

from twisted.web import resource
from twisted.internet import defer
from twisted.web.server import NOT_DONE_YET



def get_thing_name(thing: object) -> str:
    """
        Attempts to return a unique and informative name for thing

        Currently relies exclusively on __qualname__ as per https://www.python.org/dev/peps/pep-3155/

    """
    if inspect.ismethod(thing):
        return f"{thing.__qualname__}_{str(id(thing.__self__))}_{thing.__name__}"

    if hasattr(thing, "__qualname__"):
        return thing.__qualname__
    else:
        thing_name = str(id(thing)) + "_" + repr(thing) #This
        return thing_name


def sanitize_render_output(output: typing.Any) -> typing.Union[int, typing.ByteString]:
    """
        Attempt to sanitize output and return a value safe for twisted.web.server.Site to process

    :param output: the result of calling either a ViewClassResource or ViewFunctionResources render method
    :return:
    """

    returnValue = None
    import warnings

    if isinstance(output, defer.Deferred):
        returnValue = NOT_DONE_YET
    elif output is NOT_DONE_YET:
        returnValue = NOT_DONE_YET
    elif isinstance(output, str):
        returnValue = output.encode("utf-8")
    elif isinstance(output, int):
        returnValue = str(output).encode("utf-8")
    elif isinstance(output, bytes):
        returnValue = str(output).encode("utf-8")
    else:
        raise RuntimeError(f"render outputted {type(output)}, expected bytes,str,int, or NOT_DONE_YET")

    assert isinstance(returnValue, bytes) or returnValue == NOT_DONE_YET, f"Bad response data {type(returnValue)}-{returnValue!r}"

    return returnValue