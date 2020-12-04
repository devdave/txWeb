"""
    Base, Default, and generic Debug error handlers for txweb.


"""
from __future__ import annotations
import typing as T
from pathlib import Path
import linecache
from dataclasses import dataclass

from twisted.python.failure import Failure
from twisted.python.compat import intToBytes

from txweb.log import getLogger
from ... import http_codes
from . import html
from ..str_request import StrRequest
from txweb.lib.str_request import StrRequest


@dataclass
class FormattedFrame(object):
    name: bytes
    file: Path
    line_no: int
    line: bytes


class StackFrame(T.NamedTuple):
    funcName: str
    fileName: str
    lineNumber: int
    localsItems: T.Dict[str, T.Any]
    globalsItems: T.Dict[str, T.Any]


log = getLogger(__name__)


class BaseHandler(object):
    """
        TODO - Look into using twisted/zope's interface system

        Base/example class of an error handler.
    """

    def __init__(self, application):
        self.application = application

    def __call__(self, request: StrRequest, error: Failure) -> T.Union[None, bool]:
        """

        :param request:  Provided to allow managing the connection (writing, http code, etc).
        :param reason:
        :return: Return False if the handler was unable to handle the error
        """
        # noinspection PyBroadException
        try:
            return self.process(request, error)
        except Exception as exc:
            log.error("PANIC - There was an exception in the error handler.")
            request.ensureFinished()
            raise exc

    def process(self, request: StrRequest, error: Failure) -> T.Union[None, bool]:  # pragma: no cover
        raise NotImplementedError("Attempting to use Base error handler")


# noinspection PyMissingConstructor
class DefaultHandler(BaseHandler):
    """
        Primarily focused with handling 3xx HTTP exception/codes thrown by the application.

    """

    def __init__(self, enable_debug=False):

        self.enable_debug = enable_debug

    def process(self, request: StrRequest, reason: Failure) -> bool:
        """
            As mentioned in class docblock, primary focus is handling HTTPCode exceptions thrown by the application.

            If the request/response factory has already started writing to the client, this halts all error processing
             and throws the exception.

            else if a HTTPCode exception/error it redirects for 3xx codes
            OR it writes the code and message to the client
            (Eg HTTPCode500 with Internal error would throw 500 "Internal server error")

            else it sends a 500 HTTP response and then raises the exception back into the user application.

        :param request:
        :param reason:
        :return:
        """

        if request.startedWriting not in [0, False]:
            # There is nothing we can do, the out going stream is already tainted
            # noinspection PyBroadException
            log.error("Failed writing error message to an active stream")
            request.ensureFinished()
            reason.raiseException()

        elif isinstance(http_codes.HTTPCode, reason.type) or issubclass(reason.type, http_codes.HTTPCode):

            if issubclass(reason.type, http_codes.HTTP3xx):
                exc = reason.value
                request.redirect(exc.redirect, exc.code)
                response = html.REDIRECT_BODY.format(url=exc.redirect)
                request.writeTotal(response, code=exc.code, message=exc.message)
            else:
                exc = reason.value  # type: HTTPCode
                request.setResponseCode(exc.code, exc.message)
                request.setHeader("Content-length", intToBytes(len(exc.message)))
                request.write(exc.message)

        else:
            request.setResponseCode(500, b"Internal server error")
            log.debug(f"Non-HTTPCode error was caught: {reason.type} - {reason.value}")
            request.ensureFinished()
            reason.raiseException()

        request.ensureFinished()
        return True


class DebugHandler(BaseHandler):  # pragma: no cover
    """
        TODO - To finish

        Mimic flask's exception rendering system with some minor caveats.

        Errors are held in resident/session memory if possible.
        Errors can be reaccessed as necessary
        Errors time out after 5 minutes of activity
        No more than 3 errors can be held in memory at one time
        The same error is not stored more than once to avoid repeats pushing out the other
        saved errors.

        ##Cool to have
        * stack trace local/global evaluations similar to flask
        * pycharm integration (no idea if this is possible)

        ## Great to have
        * Trim errors down to JUST application code, so tracebacks don't dive all the way into twisted and
        * txweb beyond the first or second frame.

    """
    def process(self, request: StrRequest, reason: Failure) -> None:
        error_items = []
        for formatted_frame in self.format_stack(reason.frames):
            error_items.append(html.ERROR_ITEM.format(**formatted_frame))

        error_list = html.ERROR_LIST.format(error_items="\n".join(error_items))

        content = html.ERROR_CONTENT.format(digest=repr(reason.value), error_list=error_list)
        body = html.ERROR_BODY.format(content=content)

        if issubclass(reason.type, HTTPCode):
            request.setResponseCode(reason.value.code, reason.value.message)
        else:
            request.setResponseCode(500, "Internal server error")

        request.write(body)
        request.ensureFinished()

    @staticmethod
    def format_stack(frames: T.List[StackFrame]) -> T.Generator[T.Dict[str, T.Any]]:
        for frame in frames:
            yield FormattedFrame(
                name=frame[0].encode("UTF-8"),
                file=Path(frame[1]),
                line_no=frame[2],
                line=linecache.get(frame[2])
            )

        linecache.clearcache()
