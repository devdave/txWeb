# txweb imports
from txweb import resources as txw_resources
from txweb.util.basic import get_thing_name
from txweb.util.str_request import StrRequest
from txweb import view_class_assembler as vca
from txweb.errors import UnrenderableException

# twisted imports
from twisted.python import compat
from twisted.web import resource
from twisted.web import server
from twisted.web.server import Request
from twisted.web.resource import NoResource
from twisted.web import static

# Werkzeug routing import
from werkzeug import routing as wz_routing

# stdlib
import typing
import typing as T
import inspect
from collections import OrderedDict
import warnings

# given
#    website.add("/<foo:str>/<bar:int")
#    view_function(request, foo, bar)
# EndPointCallable should match `view_function`
EndpointCallable = typing.NewType("InstanceCallable",
                                  typing.Callable[
                                      [Request,
                                       typing.Optional[typing.Iterable],
                                       typing.Optional[typing.Dict],
                                       ], typing.Union[str, int]])


class GenericError(resource.Resource):

    isLeaf: typing.ClassVar[typing.Union[bool, int]] = True

    # noinspection PyMissingConstructor
    def __init__(self, message: str, error_code: typing.Optional[int] = 500):
        self.message = message  # type: typing.Text
        self.error_code = error_code  #type: int

    def render(self):
        raise NotImplementedError("TODO")


class RoutingResource(resource.Resource):

    FAILURE_RSRC_CLS = GenericError # type: typing.ClassVar[GenericError]

    def __init__(self, site, on_error: T.Optional[resource.Resource] = None):

        # TODO - Type hinting site is kind of a chicken vs egg thing as site is declared afterwards

        resource.Resource.__init__(self) #this basically just ensures that children is added to self

        self.site = site # type: WebSite
        self._endpoints = OrderedDict() # type: typing.Dict[str, resource.Resource]
        self._instances = OrderedDict() # type: typing.Dict[str, object]
        self._route_map = wz_routing.Map() # type: wz_routing.Map
        self._error_resource = self.FAILURE_RSRC_CLS if on_error is None else on_error # type: resource.Resource

    def setErrorResource(self, error_resource: resource.Resource):
        self._error_resource = error_resource

    def iter_rules(self) -> T.Generator:
        return self._route_map.iter_rules()

    def add(self, route_str:str, **kwargs:T.Dict[str, T.Any]):

        assert "endpoint" not in kwargs, \
            "Undefined behavior to use RoutingResource.add('/some/route/', endpoint='something', ...)"
        assert isinstance(route_str, str) is True, "add must be called with RoutingResource.add('/some/route/', **...)"

        # todo swap object for
        def processor(original_thing: T.Union[EndpointCallable, object]) -> T.Union[EndpointCallable, object]:

            endpoint_name = get_thing_name(original_thing)

            common_kwargs = {"endpoint":endpoint_name, "thing":original_thing, "route_kwargs":kwargs}

            if inspect.isclass(original_thing) and issubclass(original_thing, resource.Resource):
                if hasattr(original_thing, "isLeaf") and getattr(original_thing, "isLeaf") not in [True, 1]:
                    """
                        If a resource doesn't handle getResourceFor correctly, this can lead to always returning a
                        NoResource found error.
                    """
                    warnings.warn(
                        f"Added resource {original_thing}.isLeaf is {getattr(original_thing, 'isLeaf')!r}?",
                        RuntimeWarning
                    )

                self._add_resource_cls(route_str, **common_kwargs)
            elif isinstance(original_thing, resource.Resource):
                self._add_resource(route_str, **common_kwargs)
            elif inspect.isclass(original_thing):
                self._add_class(route_str, **common_kwargs)
            elif inspect.isfunction(original_thing) is True or inspect.ismethod(original_thing) is True:
                self._add_callable(route_str, **common_kwargs)
            else:
                raise ValueError(f"Received {original_thing} but expected callable|Object|twisted.web.resource.Resource")

            # return whatever was decorated unchanged
            # the Resource.getChildForRequest is completely shortcircuited so
            # that a viewable class could be inherited in userland
            return original_thing

        return processor

    def _add_callable(self, route_str:str,
                      endpoint:str=None,
                      thing:T.Union[EndpointCallable, object]=None,
                      route_kwargs:T.Dict[str,T.Any]=None):
        """

        :param route_str: a valid path for werkzeug routing
        :param endpoint: a unique str identifier for thing
        :param thing: either a function or a bound method
        :param route_kwargs: optional dictionary intended for werkzeug.routing.Rule
        :return:
        """
        route_kwargs = route_kwargs if route_kwargs is not None else {}
        new_rule = wz_routing.Rule(route_str, endpoint=endpoint, **route_kwargs)
        view_resource = txw_resources.ViewFunctionResource(thing)
        self._endpoints[endpoint] = view_resource

        self._route_map.add(new_rule)

    def _add_class(self, route_str: T.AnyStr,
                   endpoint: T.AnyStr = None,
                   thing:T.Union[object,T.Callable] = None,
                   route_kwargs: T.Dict[str, T.Any] = None):

        if vca.is_renderable(thing) is False:
            raise UnrenderableException(f"{thing.__name__!r} is missing exposed methods or a render method")

        if vca.has_exposed(thing):
            result = vca.view_assembler(route_str, thing, route_kwargs)
            self._instances[endpoint] = result.instance
            self._endpoints.update(result.endpoints)
            self._route_map.add(result.rule)
        else:
            instance = self._instances[endpoint] = thing(**route_kwargs.get("inits_kwargs",{}))
            self._route_map.add(wz_routing.Rule(route_str, endpoint=endpoint))
            self._endpoints[endpoint] = txw_resources.ViewClassResource(thing, instance)

    def _add_resource_cls(self, route_str, endpoint=None, thing=None, route_kwargs=None):
        route_kwargs = route_kwargs if route_kwargs is not None else {}
        if endpoint not in self._instances:
            self._instances[endpoint] = thing()
        self._add_resource(route_str, endpoint=endpoint, thing=self._instances[endpoint], route_kwargs=route_kwargs)

    def _add_resource(self, route_str, endpoint=None, thing=None, route_kwargs=None):
        route_kwargs = route_kwargs if route_kwargs is not None else {}

        new_rule = wz_routing.Rule(route_str, endpoint=endpoint, **route_kwargs)
        self._endpoints[endpoint] = thing

        self._route_map.add(new_rule)


    def add_directory(self, route_str, dir_path):

        directoryResource = txw_resources.Directory(dir_path)
        fixed_route = route_str + "<path:path>"
        endpoint = get_thing_name(directoryResource)
        newRule = wz_routing.Rule(fixed_route, endpoint=endpoint, methods=["GET","HEAD"], defaults={"path":"/"})
        self._endpoints[endpoint] = directoryResource
        self._route_map.add(newRule)



    def _build_map(self, pathEl, request):

        from twisted.web.wsgi import _wsgiString

        map_bind_kwargs = {}

        server_port = getattr(request.getHost(), "port", 0)

        if server_port not in [443, 80, 0]:
            map_bind_kwargs["server_name"] = request.getRequestHostname() + b":" + compat.intToBytes(server_port)
        else:
            map_bind_kwargs["server_name"] = request.getRequestHostname()

        map_bind_kwargs["script_name"] = b"/".join(request.prepath) if request.prepath else b"/"

        #TODO add strict slash check flag to here or to website.add
        if map_bind_kwargs["script_name"].startswith(b"/") is False:
            map_bind_kwargs["script_name"] = b"/" + map_bind_kwargs["script_name"]

        map_bind_kwargs["path_info"] = request.path
        map_bind_kwargs['url_scheme'] = "https" if request.isSecure() else "http"
        map_bind_kwargs['default_method'] = request.method

        map_bind_kwargs = {k:v.decode("utf-8") for k,v in map_bind_kwargs.items() if isinstance(v, bytes)}

        return self._route_map.bind(**map_bind_kwargs)



    def getChildWithDefault(self, pathEl, request):

        map = self._build_map(pathEl, request)

        try:
            (rule, kwargs) = map.match(return_rule=True)
        except wz_routing.NotFound:
            rule = None

        if rule:
            request.rule = rule
            request.route_args = kwargs
            return self._endpoints[rule.endpoint]
        else:
            return NoResource()


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

    def add(self, route_str: str, **kwargs: typing.Dict[str, typing.Any]) -> typing.Callable:
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
                     **kwargs: typing.Dict[str, typing.Any]) -> resource.Resource:
        return self.resource.add(route_str, **kwargs)(rsrc)

    def expose(self, route_str, **route_kwargs):
        return vca.expose(route_str, **route_kwargs)



    def getResourceFor(self, request):
        found_resource = super().getResourceFor(request)

        if found_resource is None or isinstance(found_resource, NoResource):
            return self.no_resource_cls()
        else:
            return found_resource


