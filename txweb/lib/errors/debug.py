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

from txweb.lib.str_request import StrRequest
from txweb.log import getLogger
from ... import http_codes
from ..str_request import StrRequest
from . import html
from .base import BaseHandler


@dataclass
class FormattedFrame:
    name: bytes
    file: Path
    line_no: int
    line: bytes

@dataclass(frozen=True, unsafe_hash=True)
class StackFrame:
    funcName: str
    fileName: str
    lineNumber: int
    localsItems: T.Dict[str, T.Any]
    globalsItems: T.Dict[str, T.Any]


log = getLogger(__name__)

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
    def process(self, request: StrRequest, reason: Failure) -> T.Union[None, bool]:
        error_items = []
        for formatted_frame in self.format_stack(reason.frames):
            error_items.append(html.ERROR_ITEM.format(**formatted_frame))

        error_list = html.ERROR_LIST.format(error_items="\n".join(error_items))

        content = html.ERROR_CONTENT.format(digest=repr(reason.value), error_list=error_list)
        body = html.ERROR_BODY.format(content=content)

        if issubclass(reason.type, http_codes.HTTPCode):
            request.setResponseCode(reason.value.code, reason.value.message)
        else:
            request.setResponseCode(500, "Internal server error")

        request.write(body)
        request.ensureFinished()

    @staticmethod
    def format_stack(frames: T.List[StackFrame]) -> T.Generator[T.Dict[str, T.Any]]:
        """
        Given a twisted Failure frames list, create a generator that yields FormattedFrame's for easier
         consumption by a jinja2 template.
        :param frames:
        :return:
        """
        for frame in frames:
            yield FormattedFrame(
                name=frame[0].encode("UTF-8"),
                file=Path(frame[1]),
                line_no=frame[2],
                line=linecache.get(frame[2])
            )

        linecache.clearcache()
