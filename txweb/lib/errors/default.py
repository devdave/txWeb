"""
    Base, Default, and generic Debug error handlers for txweb.


"""
from __future__ import annotations
import typing as T

from twisted.python.failure import Failure
from twisted.python.compat import intToBytes

from txweb.lib.str_request import StrRequest
from txweb.log import getLogger
from ... import http_codes
from . import html
from ..str_request import StrRequest
from .base import BaseHandler


log = getLogger(__name__)





# noinspection PyMissingConstructor
class DefaultHandler(BaseHandler):
    """
        Primarily focused with handling 3xx HTTP exception/codes thrown by the application.

    """

    def process(self, request: StrRequest, reason: Failure) -> T.Union[None, bool]:
        """
            As mentioned in class docblock, primary focus is handling HTTPCode exceptions thrown by the application.

            If the request/response factory has already started writing to the client, this halts all error processing
             and throws the exception.

            else if a HTTPCode exception/error it redirects for 3xx codes
            OR it writes the code and message to the client
            (Eg HTTPCode500 with Internal error would throw 500 "Internal server error")

            else it sends a 500 HTTP response and then raises the exception back into the user application.

        Parameters
        ----------
        request: StrRequest
        reason: Failure

        Returns
        -------
        False on failure to handle error
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


