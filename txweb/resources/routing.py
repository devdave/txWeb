from txweb.errors import UnrenderableException
from txweb.util.url_converter import DirectoryPath
from txweb.util.basic import get_thing_name
from txweb.lib.str_request import StrRequest
from txweb import resources as txw_resources
from ..lib import view_class_assembler as vca
from txweb import errors as HTTP_Errors

from twisted.web import resource
from twisted.python import compat

# Werkzeug routing import
from werkzeug import routing as wz_routing

from .generic import GenericError

from collections import OrderedDict
import typing as T
import inspect
import warnings
from pathlib import Path

# given
#    website.add("/<foo:str>/<bar:int")
#    view_function(request, foo, bar)
# EndPointCallable should match `view_function`
EndpointCallable = T.NewType("InstanceCallable",
                                  T.Callable[
                                      [StrRequest,
                                       T.Optional[T.Iterable],
                                       T.Optional[T.Dict],
                                       ], T.Union[str, int]])



class RoutingResource(resource.Resource):

    FAILURE_RSRC_CLS = GenericError # type: typing.ClassVar[GenericError]

    def __init__(self, on_error: T.Optional[resource.Resource] = None):


        resource.Resource.__init__(self)

        self._site = None
        self._endpoints = OrderedDict() # type: typing.Dict[str, resource.Resource]
        self._instances = OrderedDict() # type: typing.Dict[str, object]
        self._route_map = wz_routing.Map() # type: wz_routing.Map
        self._error_resource = self.FAILURE_RSRC_CLS if on_error is None else on_error # type: resource.Resource

        self._route_map.converters['directory'] = DirectoryPath

    @property
    def site(self):
        return self._site

    @site.setter
    def site(self, site):
        self._site = site
        return self._site

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


    def add_resource(self, route_str, resource_object, endpoint=None, route_kwargs=None):
        route_kwargs = route_kwargs or {}
        endpoint = endpoint if endpoint is not None else get_thing_name(resource_object)

        new_rule = wz_routing.Rule(route_str, endpoint=endpoint, **route_kwargs)
        if endpoint not in self._endpoints:
            self._endpoints[endpoint] = resource_object

        self._route_map.add(new_rule)

        return resource_object

    def _add_resource(self, route_str, endpoint=None, thing=None, route_kwargs=None):
        route_kwargs = route_kwargs if route_kwargs is not None else {}

        new_rule = wz_routing.Rule(route_str, endpoint=endpoint, **route_kwargs)
        self._endpoints[endpoint] = thing

        self._route_map.add(new_rule)

    def add_directory(self, route_str: str, dir_path: T.Union[str, Path]) -> txw_resources.Directory:

        if route_str.endswith("/") is False:
            route_str += "/"

        directory_resource = txw_resources.Directory(dir_path)
        endpoint = get_thing_name(directory_resource)
        self._endpoints[endpoint] = directory_resource

        fixed_rule = wz_routing.Rule(route_str,
                                     endpoint=endpoint,
                                     methods=["GET", "HEAD"],
                                     defaults={"postpath":""})

        instrumented_rule = wz_routing.Rule(route_str + "<directory:postpath>",
                                            endpoint=endpoint,
                                            methods=["GET","HEAD"])

        self._route_map.add(fixed_rule)
        self._route_map.add(instrumented_rule)

        return directory_resource



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

        map_bind_kwargs = {k: v.decode("utf-8") for k, v in map_bind_kwargs.items() if isinstance(v, bytes)}

        return self._route_map.bind(**map_bind_kwargs)



    def getChildWithDefault(self, pathEl, request: StrRequest):

        map = self._build_map(pathEl, request)

        try:
            (rule, kwargs) = map.match(return_rule=True)
        except wz_routing.NotFound:
            # TODO remove print
            print(f"Unable to find match for: {request.path!r}")
            raise HTTP_Errors.HTTP404()

        except wz_routing.MethodNotAllowed:
            # TODO finish error handling
            print(f"Could not find match for: {request.path!r}")
            raise HTTP_Errors.HTTP405()


        if rule:
            request.rule = rule
            request.route_args = kwargs
            if "postpath" in kwargs:
                request.postpath = [el.encode("utf-8") for el in kwargs['postpath']]
            return self._endpoints[rule.endpoint]
        else:
            raise HTTP_Errors.HTTP404()