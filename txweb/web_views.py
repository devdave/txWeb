# txweb imports
from txweb import resources as txw_resources
from txweb.util.basic import get_thing_name

# twisted imports
from twisted.python import compat
from twisted.web import resource
from twisted.web import server
from twisted.web.server import Request
from twisted.web.resource import NoResource
from twisted.web.server import NOT_DONE_YET

# Werkzeug routing import
from werkzeug import routing as wz_routing

# stdlib
import typing
import inspect
from collections import OrderedDict
import copy


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

    def __init__(self, message: str, error_code: typing.Optional[int] = 500):
        self.message = message # type: typing.Text
        self.error_code = error_code #type: int

    def render(self):
        raise NotImplementedError("TODO")


class RoutingResource(resource.Resource):

    FAILURE_RSRC_CLS = GenericError # type: typing.ClassVar[GenericError]

    def __init__(self, on_error: typing.Optional[resource.Resource] = None):
        resource.Resource.__init__(self) #this basically just ensures that children is added to self


        self._endpoints = OrderedDict() # type: typing.Dict[str, resource.Resource]
        self._instances = OrderedDict() # type: typing.Dict[str, object]
        self._route_map = wz_routing.Map() # type: wz_routing.Map
        self._error_resource = self.FAILURE_RSRC_CLS if on_error is None else on_error

    def setErrorResource(self, error_resource: resource.Resource):
        self._error_resource = error_resource

    def iter_rules(self) -> typing.Generator:
        return self._route_map.iter_rules()

    def add(self, route_str, **kwargs):

        assert "endpoint" not in kwargs, "Undefined behavior to use RoutingResource.add('/some/route/', endpoint='something', ...)"
        assert isinstance(route_str, str) is True, "add must be called with RoutingResource.add('/some/route/', **...)"

        # todo swap object for
        def processor(original_thing: typing.Union[EndpointCallable, object]) -> typing.Union[EndpointCallable, object]:

            endpoint_name = get_thing_name(original_thing)

            common_kwargs = {"endpoint":endpoint_name, "thing":original_thing, "route_args":kwargs}

            if inspect.isclass(original_thing) and issubclass(original_thing, resource.Resource):
                self._add_resource_cls(route_str, **common_kwargs)
            elif isinstance(original_thing, resource.Resource):
                self._add_resource(route_str, **common_kwargs)
            elif inspect.isclass(original_thing):
                self._add_class(route_str, **common_kwargs)
            elif inspect.isfunction(original_thing) is True:
                self._add_callable(route_str, **common_kwargs)
            else:
                ValueError(f"Recieved {original_thing} but expected callable|Object|twisted.web.resource.Resource")

            # return whatever was decorated unchanged
            # the Resource.getChildForRequest is completely shortcircuited so
            # that a viewable class could be inherited in userland
            return original_thing

        return processor

    def _add_callable(self, route_str, endpoint=None, thing=None, route_args=None):
        route_args = route_args if route_args is not None else {}
        new_rule = wz_routing.Rule(route_str, endpoint=endpoint, **route_args)
        view_resource = txw_resources.ViewFunctionResource(thing)
        self._endpoints[endpoint] = view_resource

        self._route_map.add(new_rule)

    def _add_class(self, route_str, endpoint=None, thing=None, route_args=None):

        route_args = route_args if route_args is not None else {}
        new_rule = wz_routing.Rule(route_str, endpoint=endpoint, **route_args)

        # Avoid making multiple instances of a routed view class
        #  and avoid reinstantiaing thing.__init__ in case it depends on that
        #  to configure itself
        if endpoint not in self._instances:
            self._instances[endpoint] = thing()

        view_resource = txw_resources.ViewClassResource(thing, self._instances[endpoint])
        self._endpoints[endpoint] = view_resource

        self._route_map.add(new_rule)

    def _add_resource_cls(self, route_str, endpoint=None, thing=None, route_args=None):
        route_args = route_args if route_args is not None else {}
        if endpoint not in self._instances:
            self._instances[endpoint] = thing()
        self._add_resource(route_str, endpoint=endpoint, thing=self._instances[endpoint], route_args=route_args)

    def _add_resource(self, route_str, endpoint=None, thing=None, route_args=None):
        route_args = route_args if route_args is not None else {}

        new_rule = wz_routing.Rule(route_str, endpoint=endpoint, **route_args)
        self._endpoints[endpoint] = thing

        self._route_map.add(new_rule)

    def _buildMap(self, pathEl, request):

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

        request.map = self._buildMap(pathEl, request)

        try:

            (rule, kwargs) = request.map.match(return_rule=True)
        except wz_routing.NotFound:
            rule = None

        if rule:
            request.rule = rule
            request.route_args = kwargs
            return self._endpoints[rule.endpoint]
        else:
            raise NotImplemented("TODO handle 404 logic")


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

        self._route_map = wz_routing.Map()
        self._match_route = None
        self._instance_map = {} # type: typ.Dict[str, typ.Any ] # todo make a txweb BaseView class
        self._view_map = {} # type: typ.Dict[str, EndpointCallable]

        self.double_slash_warning = True

        self.no_resource_cls = NoResource
        self.jinja2_env = None # type: jinja2.Environment


        server.Site.__init__(self, RoutingResource())


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


website = WebSite()
add = website.add
