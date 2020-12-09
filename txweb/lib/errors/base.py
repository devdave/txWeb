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

        Parameters
        ----------
        request: StrRequest
        The request and current response to a failed transaction.

        error: Failure


        Returns
        -------
        False signals the errorhandler failed to properly handle the error.
        None or True signals the errorhandler was successfull

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

        Parameters
        ----------
        request
        error

        Returns
        -------

        """
        raise NotImplementedError("Attempting to use Base error handler")
