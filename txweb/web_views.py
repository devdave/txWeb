from __future__ import annotations
# txweb imports
from txweb import resources as txw_resources
from txweb.util.str_request import StrRequest
from txweb import view_class_assembler as vca
from txweb.resources import RoutingResource
from txweb import errors as HTTP_Errors


# twisted imports
from twisted.web import resource
from twisted.web import server
from twisted.web.resource import NoResource

import typing as T
if T.TYPE_CHECKING:
    # No executable intended for type hints only
    import pathlib


class _RoutingSiteConnectors(server.Site):
    """
        Purpose: provide hooks to the RoutingResource assigned to self.resource
    """

    def add(self, route_str: str, **kwargs: T.Dict[str, T.Any]) -> T.Callable:
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
                     **kwargs: T.Dict[str, T.Any]) -> resource.Resource:
        return self.resource.add(route_str, **kwargs)(rsrc)

    def expose(self, route_str, **route_kwargs):
        return vca.expose(route_str, **route_kwargs)

class WebSite(_RoutingSiteConnectors):
    """
        Public side of the web_views class collection.

        Purpose: Hook into the resource|getResourceFor

    """

    def __init__(self):

        server.Site.__init__(self, RoutingResource(self), requestFactory=StrRequest)
        self._errorHandler = self._genericErrorHandler

    def setNoResourceCls(self, no_resource_cls):
        self.no_resource_cls = no_resource_cls


    def _getResourceFor(self, request):
        found_resource = super().getResourceFor(request)
        if found_resource is None:
            raise HTTP_Errors.HTTP404()
        else:
            return found_resource


    def onError(self, func):
        self._errorHandler = func

    @staticmethod
    def _genericErrorHandler(site, exc):
        if isinstance(exc, HTTP_Errors.HTTP404):
            return resource.NoResource()
        else:
            return resource.ErrorPage(brief="Unhandled error", detail=repr(exc), status=500)

    def getResourceFor(self, request):

        try:
            return self._getResourceFor(request)
        except HTTP_Errors.HTTP303:
            raise RuntimeError("This should have been caught by RoutingResource")
        except HTTP_Errors.HTTPCode as exc:
            return self._errorHandler(self, exc)



