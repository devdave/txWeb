from __future__ import annotations
# txweb imports
import txweb
from txweb import resources as txw_resources
from txweb.lib.str_request import StrRequest
from txweb.lib import view_class_assembler as vca
from txweb.resources import RoutingResource
from txweb import errors as HTTP_Errors

#Third party
############
import jinja2

# twisted imports
from twisted.web import resource
from twisted.python import failure
from twisted.web import server
from twisted.web.resource import NoResource

#stdlib
from logging import getLogger
import pathlib


log = getLogger(__name__)

import typing as T
if T.TYPE_CHECKING:
    # No executable intended for type hints only
    import pathlib

ResourceView = T.Type["_ResourceThing"]

LIBRARY_TEMPLATE_PATH = pathlib.Path(txweb.__file__).parent / "templates"

class _RoutingSiteConnectors(server.Site):
    """
        Purpose: provide hooks to the RoutingResource assigned to self.resource
    """
    resource: RoutingResource



    def add(self, route_str: str, **kwargs: T.Optional[T.Dict[str, T.Any]]) -> ResourceView:
        """

        :param route_str: A valid werkzeug routing url
        :param kwargs: optional keyword arguments for werkzeug routing
        :return:
        """
        return self.resource.add(route_str, **kwargs)

    def add_file(self, route_str: str, filePath: str, defaultType="text/html") -> txw_resources.SimpleFile:
        """
        Just a simple helper for a common task of serving individual files

        :param route_str: A valid URI route string
        :param filepath: An absolute or relative path to a file to be served over HTTP
        :param default_type: What content type should a file be served as
        :return: twisted.web.static.File
        """
        return self.add_resource(route_str, txw_resources.SimpleFile(filePath, defaultType=defaultType))

    def add_directory(self, route_str: str, dirPath: T.Union[str, pathlib.Path]) -> txw_resources.Directory:

        return self.resource.add_directory(route_str, dirPath)



    def add_resource(self, route_str: str,
                     rsrc: resource.Resource,
                     **kwargs: T.Dict[str, T.Any]) -> ResourceView:
        return self.resource.add(route_str, **kwargs)(rsrc)

    def expose(self, route_str, **route_kwargs) -> T.Callable:
        return vca.expose(route_str, **route_kwargs)


class WebSite(_RoutingSiteConnectors, object):
    """
        Public side of the web_views class collection.

        Purpose: Hook into the resource|getResourceFor

    """
    _errorHandler: T.Callable[['Website', StrRequest, failure.Failure], None]

    def __init__(self):
        super(WebSite, self).__init__(RoutingResource(self), requestFactory=StrRequest)
        self._errorHandler = WebSite.defaultSiteErrorHandler
        self._lastError = None

    def processingFailed(self, request: StrRequest, reason: failure.Failure):

        self._lastError = reason
        try:
            self._errorHandler(self, request, reason)
        except Exception as exc:
            #Dear god wtf went wrong?
            log.exception(f"Exception occurred while handling {reason}")

        if not request.finished:
            request.setResponseCode(500)
            request.finish()


    @staticmethod
    def defaultSiteErrorHandler(site: 'WebSite', request: StrRequest, reason: failure.Failure):

        template_path = (LIBRARY_TEMPLATE_PATH / "debug_error.html")  # type: pathlib.Path
        assert template_path.exists and template_path.is_file(), f"Unable to find library template: {template_path}"
        template = jinja2.Template(template_path.read_text())

        traceback = reason.getTraceback() if site.displayTracebacks else None

        if issubclass(reason.type, HTTP_Errors.HTTP3xx):
            code = reason.value.code
            message = "HTTP Redirect"
            buffer = b""
            request.setHeader("Location", reason.value.redirect)
        elif traceback is not None and isinstance(reason.type, HTTP_Errors.HTTP405):
            traceback = None
        elif issubclass(reason.type, HTTP_Errors.HTTPCode):
            code = reason.value.code
            message = reason.value.message if traceback else "Error"
            buffer = template.render(code=code, message=message, traceback=traceback)
        else:
            code = 500
            message = "Processing aborted"
            buffer = template.render(code=code, message=message, traceback=traceback)

        request.setHeader(b'content-type', b"text/html")
        request.setHeader(b'content-length', str(len(buffer)).encode("utf-8"))
        request.setResponseCode(code)
        request.write(buffer)
        request.finish()


















