"""
    Application is a common interface to Texas's various components

    The Application object logic has been broken apart into two mixin like classes and the main Application class.

    1. Routing logic (adding new routes/resources to the URL router) `ApplicationRoutingHelperMixin`
    2. Error handling `ApplicationErrorHandlingMixin`
    3. General utilities and resources ( website, router, reactor, etc) `Application`


"""
from __future__ import annotations

# Stdlib
from pathlib import Path
import typing as T
import sys
import inspect
import functools
# 3rd party
from twisted.internet.tcp import Port
from twisted.internet.posixbase import PosixReactorBase
from twisted.internet import reactor  # type: PosixReactorBase
from twisted.python.compat import intToBytes
from twisted.web.server import NOT_DONE_YET
from twisted.web.static import File
from twisted.python import failure

try:
    import autobahn
except ImportError:
    AUTOBAHN_MISSING = True
else:
    AUTOBAHN_MISSING = False
    from .lib.at_wsprotocol import AtWSProtocol
    from .lib.message_handler import MessageHandler
    from .lib.routed_factory import RoutedWSFactory

# Application
from .log import getLogger
from .resources import RoutingResource, SimpleFile, Directory
from .lib import StrRequest, expose_method, set_prefilter, set_postfilter
from .web_views import WebSite
from .http_codes import HTTPCode
from .lib.errors.handler import DefaultHandler, DebugHandler, BaseHandler


HERE = Path(__file__).parent
WS_STATIC_LIB = HERE / "websocket_static_libraries"

log = getLogger(__name__)

if T.TYPE_CHECKING:

    ArbitraryListArg = T.NewType("ArbitraryListArg", T.List[T.Any])
    ArbitraryKWArguments = T.NewType("ArbitraryKWArguments", T.Optional[T.Dict[str, T.Any]])

    WebCallable = T.NewType("WebCallable", T.Callable[[StrRequest, ArbitraryListArg], T.Union[str, bytes]])
    CallableToResourceDecorator = T.NewType("CallableToResourceDecorator", T.Callable[[WebCallable], WebCallable])

    ErrorHandler = T.NewType("ErrorHandler", T.Callable[[StrRequest, failure.Failure], T.Union[bool, None]])


class ApplicationWebsocketMixin(object):

    WS_EXPOSED_FUNC = "WS_EXPOSED_FUNC"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ws_endpoints = {}
        self.ws_factory = None
        self.ws_resource = None
        self.ws_instances = {}

    def enable_websockets(self, url, route):
        if AUTOBAHN_MISSING is True:
            raise EnvironmentError("Unable to provide websocket support without autobahn installed/present")

        self.ws_factory = RoutedWSFactory(url, self.ws_endpoints)
        self.ws_resource = WebSocketResource(self.ws_factory)
        self.add_resource(route, self.ws_resource)

    def ws_add(self, name, assign_args=False) -> T.Callable[[WSEndpoint], WSEndpoint]:

        def processor(func: WSEndpoint) -> WSEndpoint:
            self.ws_endpoints[name] = func
            if assign_args is True:
                func = self.websocket_function_arguments_decorator(func)
            return func

        return processor

    # noinspection SpellCheckingInspection
    def ws_sharelib(self, route_str="/lib"):
        self.add_staticdir2(route_str, WS_STATIC_LIB)

    def ws_class(self, kls):
        kls_name = kls.__name__.lower()
        if kls_name in self.ws_instances:
            raise ValueError(f"Websocket name: {kls_name} class is already registered!")

        self.ws_instances[kls_name] = kls(self)

        methods = [member
                   for member in inspect.getmembers(self.ws_instances[kls_name])
                   if inspect.ismethod(member[1]) and hasattr(member[1], self.WS_EXPOSED_FUNC)]

        for name, method in methods:
            self.ws_endpoints[f"{kls_name}.{name.lower()}"] = method

        return kls

    @staticmethod
    def websocket_class_arguments_decorator(func):
        params = inspect.signature(func).parameters
        arg_keys = {}
        for param_name, param in params.items():  # type: inspect.Parameter
            if param.default is not inspect.Parameter.empty:
                if param.name in ["connection", "message"]:
                    raise TypeError(f"Cannot use assign_args when using keyword arguments `connection` or `message`: {param.name}")
                arg_keys[param_name] = param.default

        if "connection" not in params or "message" not in params:
            raise TypeError("ws_expose convention expects (self, connection, message, **kwargs)")


        @functools.wraps(func)
        def argument_decorator(parent, connection, message):
            kwargs = {}


            for arg_name, arg_default in arg_keys.items():
                kwargs[arg_name] = message.get(arg_name, arg_default)

            return func(parent, connection, message, **kwargs)

        return argument_decorator

    @staticmethod
    def websocket_function_arguments_decorator(func):
        params = inspect.signature(func).parameters
        arg_keys = {}
        for name, param in params.items():  # type: inspect.Parameter
            if param.default is not inspect.Parameter.empty:
                if param.name in ["connection", "message"]:
                    raise TypeError(
                        f"Cannot use assign_args when using keyword arguments `connection` or `message`: {param.name}")
                arg_keys[name] = param.default

        if "connection" not in params or "message" not in params:
            raise TypeError("ws_add convention expects (connection, message)")

        @functools.wraps(func)
        def argument_decorator(connection, message: MessageHandler):
            kwargs = {}

            for name, default in arg_keys.items():
                kwargs[name] = message.args(name, default=default) #TODO also use annotation for type-casting

            return func(connection, message, **kwargs)

        return argument_decorator


    def ws_expose(self, func: callable = None, assign_args=False):

        if func is None and assign_args is True:
            def processor(real_func):
                setattr(real_func, self.WS_EXPOSED_FUNC, True)
                magic_func = self.websocket_class_arguments_decorator(real_func)
                return magic_func
            return processor

        else:
            setattr(func, self.WS_EXPOSED_FUNC, True)
            return func


class ApplicationRoutingHelperMixin(object):
    """
        Provides a wrapping interface around :ref: `RoutingResource`

    """
    router:RoutingResource

    def add(self, route_str:str, **kwargs: ArbitraryKWArguments) -> CallableToResourceDecorator:
        """

        :param route_str: A valid URI (starts with a forward slash and no spaces)
        :param kwargs:
        :return:
        """
        return self.router.add(route_str, **kwargs)

    # mimic flask's API
    route = add

    def add_class(self, route_str:str, **kwargs: ArbitraryKWArguments) ->CallableToResourceDecorator:
        return self.router.add(route_str, **kwargs)


    def add_resource(self, route_str:str, resource, **kwargs):
        return self.router._add_resource(route_str, thing=resource, route_kwargs=kwargs )


    def add_file(self, route_str: str, filePath: str, defaultType="text/html") -> SimpleFile:
        """
        Just a simple helper for a common task of serving individual files

        :param route_str: A valid URI route string
        :param filepath: An absolute or relative path to a file to be served over HTTP
        :param default_type: What content type should a file be served as
        :return: twisted.web.static.File
        """
        from twisted.web.static import File as StaticFile
        assert Path(filePath).exists()
        file_resource = StaticFile(filePath)
        return self.router.add(route_str)(file_resource)

    def add_staticdir(self, route_str: str, dirPath: T.Union[str, Path], recurse = False) -> Directory:

        if route_str.endswith("/") is False:
            route_str += "/"

        directory_resource = Directory(dirPath, recurse)

        self.router.add_directory(route_str, directory_resource)

        return directory_resource

    def add_staticdir2(self, route_str: str, dirPath: T.Union[str, Path], recurse = False) -> File:

        if route_str.endswith("/") is False:
            route_str += "/"

        directory_resource = File(dirPath)

        self.router.add_directory(route_str, directory_resource)

        return directory_resource


    def expose(self, route_str, **kwargs):
        # TODO make route_str optional somehow
        return expose_method(route_str, **kwargs)

    def set_prefilter(self, func):
        return set_prefilter(func)

    def set_postfilter(self, func):
        return set_postfilter(func)


class ApplicationErrorHandlingMixin(object):
    """
    The Error processing and handling aspect of Application
    """


    error_handlers: T.Dict[str, ErrorHandler]
    default_handler_cls:BaseHandler = DefaultHandler
    enable_debug: bool
    site: WebSite

    def __init__(self, enable_debug: bool =False,  **kwargs):
        """
        :param enable_debug: Flag to decide if to use debugging tools
        """
        self.error_handlers = dict(default=self.default_handler_cls(self))
        self.enable_debug = enable_debug

        self.site.addErrorHandler(self.processingFailed)


    def handle_error(self, error_type: T.Union[HTTPCode, int, Exception, str], write_over=False) -> T.Callable:
        """
        Decorator utility to add a new :param error_type: specific handler.
        Acceptable types currently is a subclass of Exception (eg error.HTTP404) or
        a numeric HTTP error code (eg 404,500, etc).


        :param error_type:  The error to catch, either the thrown exception or a numeric HTTP CODE
        :param write_over:  Used to over ride or replace a currently set error handler.   Currently the only error
        handler set is the catch all 'default" handler which I don't recommend replacing.
        :return:
        """

        def processor(func: ErrorHandler) -> ErrorHandler:
            if error_type in self.error_handlers and write_over is False:
                old_func = self.error_handlers[error_type]
                raise ValueError(f"handle_error called twice to handle {error_type} with old {old_func} vs {func}")

            self.error_handlers[error_type] = func
            return func

        return processor

    def add_error_handler(self, handler:T.Callable, error_type: T.Union[HTTPCode, int, Exception, str], override=False):

        if error_type in self.error_handlers and override is False:
            old_func = self.error_handlers[error_type]
            raise ValueError(f"handle_error called twice to handle {error_type} with old {old_func} vs {handler}")

        self.error_handlers[error_type] = handler

    def processingFailed(self, request:StrRequest, reason: failure.Failure):

        default_handler = self.error_handlers['default']

        if reason.type in self.error_handlers:
            handler = self.error_handlers[reason.type]
        elif isinstance(reason.value, HTTPCode) and reason.value.code in self.error_handlers:
            handler = self.error_handlers[reason.value.code]
        else:
            handler = default_handler

        if handler(request, reason) is False:
            if handler == default_handler:
                raise RuntimeError(f"Default error handler {handler} returned False but it should return True")
            else:
                default_handler(request, reason)

        request.ensureFinished()

        return True






class Application(ApplicationRoutingHelperMixin, ApplicationErrorHandlingMixin, ApplicationWebsocketMixin):


    NOT_DONE_YET = NOT_DONE_YET

    def __init__(self,
                 namespace: str = None,
                 twisted_reactor: T.Optional[PosixReactorBase] = None,
                 request_factory:StrRequest=StrRequest,
                 enable_debug:bool=False
                 ):
        """
            Similar to Klein and its influence Flask, the goal is to consolidate
            technical debt into one God module antipattern class.

            Purposes:
                Provides a public API to Site, HTTPErrors, RoutingResource, and additional helpers.

            Arguments:
                namespace: the base module/package name of the application, currently intended to assist logging and debugging
                twisted_reactor: currently unused
                request_factory: currently unused
                enable_debug: Not implemented yet, switches on extra debugging tools
        """


        self._router = RoutingResource()
        self._site = WebSite(self._router, request_factory=Application.request_factory_partial(self, request_factory))
        self._router.site = self._site
        self._reactor = twisted_reactor or reactor  # type: PosixReactorBase

        self.name = namespace
        self._listening_port = None

        self._enable_debug = enable_debug
        if namespace is not None:
            self._owner_module = sys.modules[namespace]
        else:
            self.__owner_module = None


        ApplicationWebsocketMixin.__init__(self)
        ApplicationRoutingHelperMixin.__init__(self)
        # _ApplicationTemplateSupportMixin.__init__(self)
        ApplicationErrorHandlingMixin.__init__(self, enable_debug=enable_debug)


        #Hooks
        self._before_render_handlers = []
        self._after_render_handlers = []


    @staticmethod
    def request_factory_partial(app:'Application', request_kls:StrRequest):
        """
            A hack to intercept when a new http Request is created deep inside of twisted.web's protocol factory

        """

        def partial(*args, **kwargs):
            request = request_kls(*args, **kwargs)
            request.add_before_render(app._call_before_render)
            request.add_after_render(app._call_after_render)
            request.site = app.site
            return request

        return partial


    def __call__(self, namespace:str):
        """
            TODO sanity check if this is a good idea

            Allows the application namespace property to be overwritten during run time.

        """
        self.name = namespace

    @property
    def router(self) -> RoutingResource:
        return self._router

    @property
    def site(self) -> WebSite:
        return self._site

    @property
    def reactor(self) -> PosixReactorBase:
        return self._reactor

    @reactor.setter
    def reactor(self, active_reactor: PosixReactorBase):
        self._reactor = active_reactor

    def listenTCP(self, port:int, interface:str= "127.0.0.1") -> Port:
        """
            Convenience helper which adds the HTTP protocol factory to the reactor and set it to listen to the provided
            interface and port
        """
        self._listening_port = self.reactor.listenTCP(port, self.site, interface=interface)
        return self._listening_port

    def before_render(self, func: T.Callable[[StrRequest], None]):
        """
        Intended as a convenience decorator to set a global before render handler
        Arguments:
            func: a callable that expects to receive the current Request
        """
        self._before_render_handlers.append(func)
        return func

    def after_render(self, func: T.Callable[[StrRequest], None]):
        """
        Intended as a convenience decorator to set a global after render handler
        Arguments:
            func: a callable that expects to receive the current Request
        """
        self._after_render_handlers.append(func)
        return func

    def _call_before_render(self, request: StrRequest):
        for func in self._before_render_handlers:
            try:
                func(request)
            except Exception:
                log.error(f"Before render failed {func}")

    def _call_after_render(self, request: StrRequest, body:T.Union[bytes,str,int]):
        for func in self._after_render_handlers:
            try:
                func(request)
            except Exception:
                log.error(f"After render failed {func}")




