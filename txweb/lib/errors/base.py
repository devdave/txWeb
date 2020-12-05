"""
    Reference example for a error handler
"""
from __future__ import annotations
import typing as T

from twisted.python.failure import Failure

from txweb.log import getLogger
from txweb.lib.str_request import StrRequest

log = getLogger(__name__)

class BaseHandler:
    """

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
        """
        Just a stub

        :param request:
        :param error:
        :return:
        """
        raise NotImplementedError("Attempting to use Base error handler")