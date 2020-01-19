from __future__ import annotations


from twisted.python.failure import Failure


from txweb.log import getLogger
from txweb.errors import HTTPCode
from . import html
from txweb.lib.str_request import StrRequest

import typing as T
from pathlib import Path
import linecache


class FormattedFrame(T.NamedTuple):
    name: bytes
    file: Path
    line_no: int
    line: bytes

class StackFrame(T.NamedTuple):
    funcName:str
    fileName:str
    lineNumber:int
    localsItems:T.Dict[str,T.Any]
    globalsItems:T.Dict[str, T.Any]

if T.TYPE_CHECKING:
    from twisted.python.failure import Failure
    from ..str_request import StrRequest




log = getLogger(__name__)

class Base(object):

    def __init__(self, application):
        self.application = application

    def __call__(self, request: StrRequest, reason:Failure) -> None:
        try:
            self.process(request, reason)
        except:
            log.exception("PANIC - There was an exception in the error handler.")
            request.ensureFinished()

    def process(self, request: StrRequest, reason:Failure) -> None:
        raise NotImplementedError("Attempting to use Base error handler")

class DefaultHandler(Base):
    """
        Goal:  Delegate various errors to templates to make
            a visual error system easier to view.
    """

    def process(self, request: StrRequest, reason:Failure) -> None:

        if request.startedWriting not in [0, False]:
            # We are done, the HTTP stream to client is already tainted
            request.ensureFinished()
            return None
        else:
            if issubclass(reason.type, HTTPCode):
                request.setResponseCode(reason.value.code, message=reason.value.message)
                request.write(html.DEFAULT_BODY.format(message=reason.value.message, code=reason.value.code))
            else:
                request.write(html.DEFAULT_BODY.format(message="Internal server error", code=500))

        request.ensureFinished()

class DebugHandler(Base):
    """
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
    def process(self, request: StrRequest, reason:Failure) -> None:
        error_items = []
        for formated_frame in self.format_stack(reason.frames):
            error_items.append(html.ERROR_ITEM.format(**formated_frame))

        error_list = html.ERROR_LIST.format(error_items="\n".join(error_items))

        content = html.ERROR_CONTENT.format(digest=repr(reason.value),error_list=error_list)
        body = html.ERROR_BODY.format(content=content)

        if issubclass(reason.type, HTTPCode):
            request.setResponseCode(reason.value.code, reason.value.message)
        else:
            request.setResponseCode(500, "Internal server error")

        request.write(body)
        request.ensureFinished()

    def format_stack(self, frames:T.List[StackFrame]) -> T.Generator[T.Dict[str, T.Any]]:
        for frame in frames:
            yield FormattedFrame(
                name=frame[0].encode("UTF-8"),
                file=Path(frame[1]),
                line_no=frame[2],
                line=linecache.get(frame[2])
            )

        linecache.clearcache()


class MissingHandler(Base):
    """
        Intended only to handle 4xx errors where the route doesn't match at all or matches
            url but not method.
    """
    pass