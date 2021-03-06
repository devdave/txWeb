"""
    The centerpiece of TxWeb is the Routing Resource which wraps around werkzeug's routing system.

"""
from collections import OrderedDict
import typing as T
import inspect
# import warnings

from twisted.web.static import File

from twisted.web import resource
from twisted.python import compat

# Werkzeug routing import
from werkzeug import routing as wz_routing


from txweb.http_codes import Unrenderable
from txweb.util.url_converter import DirectoryPath
from txweb.util.basic import get_thing_name
from txweb.lib.str_request import StrRequest

from txweb import http_codes as HTTP_Errors

from .view_function import ViewFunctionResource
from .view_class import ViewClassResource
# from .directory import Directory
from ..lib import view_class_assembler as vca
from ..log import getLogger



log = getLogger(__name__)

# given
#    website.add("/<foo:str>/<bar:int")
#    view_function(request, foo, bar)
# EndPointCallable should match `view_function`
EndpointCallable = T.NewType("InstanceCallable",
                             T.Callable[[StrRequest, T.Optional[T.Iterable], T.Optional[T.Dict], ], T.Union[str, int]])


class RoutingResource(resource.Resource):
    """
        The bridge between twisted's object graph routing system and werkzeug's url pattern
        recognition routing system.
    """

    def __init__(self, script_name: bytes = None):
        """
        The bridge between twisted's object graph routing system and werkzeug's url pattern
        recognition routing system.

        Parameters
        ----------
        script_name: bytes
            Optional ability to add a prefix to all routed URL's in case this application
                is nested inside another web app.   See CGI's SCRIPT_NAME variable.
        """

        resource.Resource.__init__(self)

        self._site = None
        self._endpoints = OrderedDict()  # type: typing.Dict[str, resource.Resource]
        self._instances = OrderedDict()  # type: typing.Dict[str, object]
        self._route_map = wz_routing.Map()  # type: wz_routing.Map
        self._route_map.converters['directory'] = DirectoryPath
        self._script_name = script_name

    @property
    def site(self):   # pragma: no cover
        """
            Return a reference to the parent site of this resource

        Returns
        -------
        web_site instance

        """
        return self._site

    @site.setter
    def site(self, site):  # pragma: no cover
        """
        TODO - Verify this is still being used.
        :param site:
        :return:
        """
        self._site = site

    def iter_rules(self) -> T.Generator:
        """
        Debug method for iterating over all of the currently set URL Rule's for the werkzeug routing map.

        """
        return self._route_map.iter_rules()

    def add(self, route_str: str, **kwargs: T.Dict[str, T.Any]):
        """
            Possibly super overloaded



        """

        if "endpoint" in kwargs:
            raise ValueError("Undefined behavior to use RoutingResource.add('/some/route/', endpoint='something', ...)")

        if isinstance(route_str, str) is False:
            raise ValueError(f"position 1 argument, route_str must be a str, got {route_str!r} instead")


        def processor(original_thing: T.Union[EndpointCallable, object]) -> T.Union[EndpointCallable, object]:

            endpoint_name = get_thing_name(original_thing)

            common_kwargs = {"endpoint": endpoint_name, "thing": original_thing, "route_kwargs": kwargs}


            # Is the thing to be added to the router a twisted Resource class?
            if inspect.isclass(original_thing) and issubclass(original_thing, resource.Resource):

                self._add_resource_cls(route_str, **common_kwargs)

            elif isinstance(original_thing, resource.Resource):

                self.add_resource(route_str, **common_kwargs)

            elif inspect.isclass(original_thing):
                self._add_class(route_str, **common_kwargs)

            elif inspect.isfunction(original_thing) is True or inspect.ismethod(original_thing) is True:
                self._add_callable(route_str, **common_kwargs)

            elif callable(original_thing):
                self._add_callable(route_str, **common_kwargs)

            else:
                raise ValueError(
                    f"Received {original_thing} but expected callable|Object|twisted.web.resource.Resource")

            # return whatever was decorated unchanged
            # the Resource.getChildForRequest is completely short circuited so
            # that a viewable class could be inherited in userland
            return original_thing

        return processor

    def _add_callable(self, route_str: str,
                      endpoint: str = None,
                      thing: T.Union[EndpointCallable, object] = None,
                      route_kwargs: T.Dict[str, T.Any] = None):
        """

        :param route_str: a valid path for werkzeug routing
        :param endpoint: a unique str identifier for thing
        :param thing: either a function or a bound method
        :param route_kwargs: optional dictionary intended for werkzeug.routing.Rule
        :return:
        """
        route_kwargs = route_kwargs if route_kwargs is not None else {}
        new_rule = wz_routing.Rule(route_str, endpoint=endpoint, **route_kwargs)
        view_resource = ViewFunctionResource(thing)
        self._endpoints[endpoint] = view_resource

        self._route_map.add(new_rule)

    def _add_class(self, route_str: T.AnyStr,
                   endpoint: T.AnyStr = None,
                   thing: T.Union[object, T.Callable] = None,
                   route_kwargs: T.Dict[str, T.Any] = None):
        """
            A view class has been provided, decorate and process it into the router.
        """

        if vca.is_renderable(thing) is False:
            raise Unrenderable(f"{thing.__name__!r} is missing exposed methods or a render method")

        if vca.has_exposed(thing):
            result = vca.view_assembler(route_str, thing, route_kwargs)
            self._instances[endpoint] = result.instance
            self._endpoints.update(result.endpoints)
            self._route_map.add(result.rule)
        else:
            instance = self._instances[endpoint] = thing(**route_kwargs.get("inits_kwargs", {}))
            self._route_map.add(wz_routing.Rule(route_str, endpoint=endpoint))
            self._endpoints[endpoint] = ViewClassResource(thing, instance)

    def _add_resource_cls(self, route_str, endpoint=None, thing=None, route_kwargs=None):
        """
            Give the class definition of a resource, instantiate it, add it to the instances list, and then
            add the instance to the routing map.

        :param self:
        :param route_str:
        :param endpoint:
        :param thing:
        :param route_kwargs:
        :return:
        """
        route_kwargs = route_kwargs if route_kwargs is not None else {}
        if endpoint not in self._instances:
            self._instances[endpoint] = thing()
        self.add_resource(route_str, endpoint=endpoint, thing=self._instances[endpoint], route_kwargs=route_kwargs)

    def add_resource(self, route_str, endpoint=None, thing=None, route_kwargs=None):
        """

        :param self:
        :param route_str:
        :param endpoint:
        :param thing:
        :param route_kwargs:
        :return:
        """
        route_kwargs = route_kwargs if route_kwargs is not None else {}
        endpoint = endpoint or get_thing_name(thing)

        new_rule = wz_routing.Rule(route_str, endpoint=endpoint, **route_kwargs)
        self._endpoints[endpoint] = thing

        self._route_map.add(new_rule)

    def add_directory(self, route_str: str, directory_resource: File) -> File:
        """
            TODO refactor.   Since I've dropped my own custom file and directory resources
             this method isn't as relevant.
        :param route_str:
        :param directory_resource:
        :return:
        """

        endpoint = repr(directory_resource)
        if endpoint not in self._endpoints:
            self._endpoints[endpoint] = directory_resource

        fixed_rule = wz_routing.Rule(route_str,
                                     endpoint=endpoint,
                                     methods=["GET", "HEAD"],
                                     defaults={"postpath": ""})

        instrumented_rule = wz_routing.Rule(route_str + "<directory:postpath>",
                                            endpoint=endpoint,
                                            methods=["GET", "HEAD"])

        self._route_map.add(fixed_rule)
        self._route_map.add(instrumented_rule)

        return directory_resource

    def _build_map(self, request):
        """
            Takes all of the information provided by the request object and adapts them to match the wsgi environment
            dictionary so that werkzeug can provide a routing map.

            It feels unfortunate/excessive that I have to build this map on each request instead of just reporting
            the changes in URL.
        :param path_element:
        :param request:
        :return:
        """

        map_bind_kwargs = {}

        server_port = getattr(request.getHost(), "port", 0)

        if server_port not in [443, 80, 0]:
            map_bind_kwargs["server_name"] = request.getRequestHostname() + b":" + compat.intToBytes(server_port)
        else:
            map_bind_kwargs["server_name"] = request.getRequestHostname()

        if self._script_name is None:
            map_bind_kwargs["script_name"] = b"/"
        else:
            map_bind_kwargs["script_name"] = self._script_name

        if map_bind_kwargs["script_name"].startswith(b"/") is False:
            map_bind_kwargs["script_name"] = b"/" + map_bind_kwargs["script_name"]

        map_bind_kwargs["path_info"] = request.path
        map_bind_kwargs['url_scheme'] = "https" if request.isSecure() else "http"
        map_bind_kwargs['default_method'] = request.method

        map_bind_kwargs = {k: v.decode("utf-8") for k, v in map_bind_kwargs.items() if isinstance(v, bytes)}

        return self._route_map.bind(**map_bind_kwargs)

    def getChildWithDefault(self, _, request: StrRequest):
        """
            Routing resource is mostly ignorant of the larger ecosystem so it either
            returns a resource OR it throws up an errors.HTTPCode
        """

        routing = self._build_map(request)

        try:
            # TODO refactor to handle HEAD requests when the only valid match support GET
            # - one bad idea is to hack on werkzeug to append the URI matching rule to MethodNotAllowed
            (rule, kwargs) = routing.match(return_rule=True)
        except wz_routing.RequestRedirect as redirect:
            log.debug("Werkzeug threw a redirect")
            raise HTTP_Errors.HTTP3xx(redirect.code, redirect.new_url, redirect.name) from redirect
        except wz_routing.NotFound as exc:
            log.debug(f"Failed to find match for: {request.path!r}")
            raise HTTP_Errors.HTTP404(exc) from exc

        except wz_routing.MethodNotAllowed as exc:
            # TODO finish error handling
            log.debug(f"Unable to find a valid match for {request.path!r} with {request.method!r}")
            raise HTTP_Errors.HTTP405(exc) from exc

        request.rule = rule
        request.route_args = kwargs
        if "postpath" in kwargs:
            # Intended to help with nested Directory resources
            request.postpath = [el.encode("utf-8") for el in kwargs['postpath']]
        return self._endpoints[rule.endpoint]
