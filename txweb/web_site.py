"""
    Currently acts as a bridge for error handling.

"""

from __future__ import annotations

#stdlib
import typing as T
import pathlib
# import copy

# twisted imports
from twisted.python import failure
from twisted.web import server

# txweb imports
import txweb
# from txweb import resources as txw_resources
from txweb.lib.str_request import StrRequest
# from txweb.lib import view_class_assembler as vca
from txweb.resources import RoutingResource
# from txweb import http_codes as HTTP_Errors
from txweb.log import getLogger


log = getLogger(__name__)

ResourceView = T.Type["_ResourceThing"]
ErrorHandler = T.NewType("ErrorHandler", T.Callable[['Website', StrRequest, failure.Failure], None])
LIBRARY_TEMPLATE_PATH = pathlib.Path(txweb.__file__).parent / "templates"

class WebSite(server.Site):
    """
        Public side of the web_views class collection.

        Purpose: provide a hook for error handling and maybe a global template system

    """
    my_log = getLogger()
    _errorHandler: ErrorHandler

    def __init__(self, routing_resource=None, request_factory=StrRequest, siteErrorHandler=None):
        routing_resource = routing_resource or RoutingResource()
        request_factory = request_factory or StrRequest

        # _RoutingSiteConnectors.__init__(self, routing_resource, requestFactory=request_factory)
        super().__init__(routing_resource, requestFactory=request_factory)

        self._errorHandler = siteErrorHandler
        self._lastError = None

        # self._before_request_render = None
        # self._after_request_render = None


    def processingFailed(self, request: StrRequest, reason: failure.Failure):
        """
            The crucial bridge that connects a request.processingFailed exception chain upward
                towards the Txweb application instance for errorhandling.
        :param request:
        :param reason:
        :return:
        """

        self._lastError = reason
        # self.my_log.error("Handling exception: {reason!r}", reason=reason)

        try:
            self._errorHandler(request, reason)
        except Exception as exc:
            #Dear god wtf went wrong?
            self.my_log.error("Exception {exc!r} occurred while handling {reason!r}", exc=exc, reason=reason)
            raise

    def setErrorHandler(self, func: ErrorHandler):
        """
            Kind of goofy, this should only be called by the Txweb application error handler so it can
            snag the failure/exception that occurred in request.render
        :param func:
        :return:
        """
        self._errorHandler = func
        return func

