# txweb imports
from txweb import resources as txw_resources
from txweb.util.str_request import StrRequest
from txweb import view_class_assembler as vca
from txweb.resources import RoutingResource



# twisted imports

from twisted.web import resource
from twisted.web import server
from twisted.web.resource import NoResource
from twisted.web import static




# stdlib
import typing as T
import inspect
from collections import OrderedDict
import warnings
from pathlib import Path










class WebSite(server.Site):
    """
        Overloads/overrides the twisted.web.server.Site classes routing logic

            standard logic for /foo/bar/widget/thing is
                site()->resource == /
                    ._children[foo resource]._children[bar resource] and etc until reaching widget or thing resource

            New logic
                callable_name = WerkZeug.map.match(route string) -> str
                self._view_map[callable](request, *args, **kwargs)

    """

    def __init__(self):

        self.double_slash_warning = True

        self.no_resource_cls = NoResource
        self.jinja2_env = None  # type: jinja2.Environment

        server.Site.__init__(self, RoutingResource(self), requestFactory=StrRequest)

    def setTemplateDir(self, path):
        import jinja2

        if self.jinja2_env is None:
            self.jinja2_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(path)
                , autoescape=jinja2.select_autoescape(["html"])
            )
        else:
            raise RuntimeError(f"website.setTemplateDir already set {self.jinja2_env}")

    def render_template(self, template_name, **context):
        if self.jinja2_env is not None:
            return self.jinja2_env.get_template(template_name).render(**context)
        else:
            raise RuntimeError(f"render_template called without using setTemplateDir first")

    def setNoResourceCls(self, no_resource_cls):
        self.no_resource_cls = no_resource_cls

    def add(self, route_str: str, **kwargs: T.Dict[str, T.Any]) -> T.Callable:
        return self.resource.add(route_str, **kwargs)

    def add_file(self, route_str: str, filePath: str, defaultType="text/html"):
        """
        Just a simple helper for a common task of serving individual files

        :param route_str: A valid URI route string
        :param filepath: An absolute or relative path to a file to be served over HTTP
        :param default_type: What content type should a file be served as
        :return: twisted.web.static.File
        """
        return self.add_resource(route_str, txw_resources.SimpleFile(filePath, defaultType=defaultType))

    def add_directory(self, route_str, dirPath: str):

        return self.resource.add_directory(route_str, dirPath)



    def add_resource(self, route_str: str,
                     rsrc: resource.Resource,
                     **kwargs: T.Dict[str, T.Any]) -> resource.Resource:
        return self.resource.add(route_str, **kwargs)(rsrc)

    def expose(self, route_str, **route_kwargs):
        return vca.expose(route_str, **route_kwargs)



    def getResourceFor(self, request):
        found_resource = super().getResourceFor(request)

        if found_resource is None or isinstance(found_resource, NoResource):
            return self.no_resource_cls()
        else:
            return found_resource


