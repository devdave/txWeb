"""
    Basic and common utility functions

"""
import inspect
import typing as T

from twisted.internet import defer
from twisted.web.server import NOT_DONE_YET


def get_thing_name(thing: T.Any) -> str:
    """
        Attempts to return a unique and informative name for a thing (function, method, class, object)
    """

    if inspect.ismethod(thing):
        return_value = "_".join([
            getattr(thing, '__qualname__'),
            str(id(getattr(thing, '__self__'))),
            getattr(thing, '__name__')
        ])
    elif hasattr(thing, "__qualname__"):
        return_value = getattr(thing, "__qualname__")
    else:
        return_value = "_".join([
            str(id(thing)),
            repr(thing)
            ])

    return return_value


def sanitize_render_output(output: T.Any) -> T.Union[int, T.ByteString]:
    """
        Attempt to sanitize output and return a value safe for twisted.web.server.Site to process

    :param output: the result of calling either a ViewClassResource or ViewFunctionResources render method
    :return: Returns either a byte string or NOT_DONE_YET (has always been an int)
    """

    if isinstance(output, defer.Deferred):
        return_value = NOT_DONE_YET
    elif output is NOT_DONE_YET:
        return_value = NOT_DONE_YET
    elif isinstance(output, str):
        return_value = output.encode("utf-8")
    elif isinstance(output, int):
        return_value = str(output).encode("utf-8")
    elif isinstance(output, bytes):
        return_value = output
    else:
        raise RuntimeError(f"render outputted {type(output)}, expected bytes,str,int, or NOT_DONE_YET")

    assert isinstance(return_value, bytes) or \
        return_value == NOT_DONE_YET,\
        f"Bad response data {type(return_value)}-{return_value!r}"

    return return_value
