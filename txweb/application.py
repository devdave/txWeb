"""
    Application is a common interface to Texas's various components

    The Application object logic has been broken apart into mixin like classes and combined into Application class.

    1. Routing logic (adding new routes/resources to the URL router) `ApplicationRoutingHelperMixin`
    2. Error handling `ApplicationErrorHandlingMixin`
    3. Websocket support
    4. General utilities and resources ( website, router, reactor, etc) `Application`


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
# from twisted.python.compat import intToBytes
from twisted.web.server import NOT_DONE_YET
from twisted.web.static import File
from twisted.python import failure

try:
    from autobahn.twisted.resource import WebSocketResource
except ImportError:
    AUTOBAHN_MISSING = True
    print("Unable to support websockets:  `pip install autobahn` to enable")
else:
    AUTOBAHN_MISSING = False
    # from .lib.wsprotocol import WSProtocol
    from .lib.message_handler import MessageHandler
    from .lib.routed_factory import RoutedWSFactory


# Application
from .log import getLogger
from .resources import RoutingResource
# from .resources import SimpleFile, Directory
from .lib import StrRequest, expose_method, set_prefilter, set_postfilter
from .web_site import WebSite
from .http_codes import HTTPCode
from .lib.errors.default import DefaultHandler, BaseHandler


HERE = Path(__file__).parent
WS_STATIC_LIB = HERE / "websocket_static_libraries"

log = getLogger(__name__)


ArbitraryListArg = T.NewType("ArbitraryListArg", T.List[T.Any])
ArbitraryKWArguments = T.NewType("ArbitraryKWArguments", T.Optional[T.Dict[str, T.Any]])

WebCallable = T.NewType("WebCallable", T.Callable[[StrRequest, ArbitraryListArg], T.Union[str, bytes]])
CallableToResourceDecorator = T.NewType("CallableToResourceDecorator", T.Callable[[WebCallable], WebCallable])
WSEndpoint = T.Callable[[MessageHandler], T.Any]
ErrorHandler = T.NewType("ErrorHandler", T.Callable[[StrRequest, failure.Failure], T.Union[bool, None]])


class ApplicationWebsocketMixin:

    WS_EXPOSED_FUNC = "WS_EXPOSED_FUNC"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ws_endpoints = {}
        self.ws_factory = None
        self.ws_resource = None
        self.ws_instances = {}

    def enable_websockets(self, url, route):
        """
            Setup websocket support for txweb

        :param url:
        :param route:
        :return:
        """
        if AUTOBAHN_MISSING is True:
            raise EnvironmentError("Unable to provide websocket support without autobahn installed/present")

        self.ws_factory = RoutedWSFactory(url, self.ws_endpoints, application=self)
        self.ws_resource = WebSocketResource(self.ws_factory)
        self.add_resource(route, self.ws_resource)

    def ws_add(self, name, assign_args=False) -> T.Callable[[WSEndpoint], WSEndpoint]:
        """
        Add a new endpoint for use with the connected websocket.

        Example usage
        ```
            @ws_add
            def my_websocket_endpoint(message):
                ...
        ```
        :param name:
        :param assign_args:
        :return:
        """

        def processor(func: WSEndpoint) -> WSEndpoint:

            if assign_args is True:
                func = self.websocket_function_arguments_decorator(func)

            self.ws_endpoints[name] = func
            return func

        return processor

    # noinspection SpellCheckingInspection
    def ws_sharelib(self, route_str="/lib"):
        """
            Adds utility libraries to the provided route str for use by client facing html javascript.
        :param route_str:
        :return:
        """
        self.add_staticdir2(route_str, WS_STATIC_LIB)

    def ws_class(self, kls=None, name: str = None):
        """
        Add an entire class of @ws_expose'd class methods as endpoints for the websocket.

        Example
        ```
            @app.ws_class
            class Foo:
                @app.expose
                def bar(message):
                    ...
        ```
            That will create a "foo.bar" endpoint

        :param kls:
        :param name: Override the default behavior of using the class.__name__ property for the base endpoint.
        :return:
        """

        def processor(kls, name=None):
            kls_name = name if name is not None else kls.__name__.lower()
            if kls_name in self.ws_instances:
                raise ValueError(
                    f"Websocket ws_class: a class with {kls_name} is already registered!  Use ws_class(name=NewName) to override.")

            self.ws_instances[kls_name] = kls(self)

            methods = [member
                       for member in inspect.getmembers(self.ws_instances[kls_name])
                       if inspect.ismethod(member[1]) and hasattr(member[1], self.WS_EXPOSED_FUNC)]

            for method_name, method in methods:
                # Always use assign_args with ws_class's
                self.ws_endpoints[f"{kls_name}.{method_name.lower()}"] = method

            return kls


        if kls is None:
            return functools.partial(processor, name=name)
        else:
            return processor(kls, name)


    @staticmethod
    def _eval_annotation(statement, func):
        """
        TODO - Figure out if there is a way to the type of an annotation without eval
        :param statement:
        :param func:
        :return:
        """
        # There is no way around using eval given how I use annotation's for type casting and conversion
        # pylint: disable=W0123
        return statement if not isinstance(statement, str) else eval(statement, vars(sys.modules[func.__module__]))


    @classmethod
    def websocket_class_arguments_decorator(cls, func):
        """
            Internal method not intended for users
        :param func:
        :return:
        """
        params = inspect.signature(func).parameters
        arg_keys = {}
        converter_keys = {}

        for param in params.values():  # type: inspect.Parameter
            if param.default is not inspect.Parameter.empty:
                if param.name in ["message"]:
                    raise TypeError(f"assign_args error: argument `message` cannot be a keyword argument: {param.name}")
                arg_keys[param.name] = param.default

                if param.annotation is not inspect.Parameter.empty:
                    converter_keys[param.name] = cls._eval_annotation(param.annotation, func)

        if "message" not in params:
            raise TypeError("ws_expose convention expects (self, message, **kwargs)")


        @functools.wraps(func)
        def method_argument_decorator(parent, message):
            kwargs = {}

            for arg_name, arg_default in arg_keys.items():
                raw_argument = message.args(arg_name, arg_default)
                converter = converter_keys.get(arg_name, None)
                if converter:
                    try:
                        kwargs[arg_name] = converter(raw_argument)
                    except (TypeError, ValueError,):
                        kwargs[arg_name] = arg_default
                else:
                    kwargs[arg_name] = raw_argument

            return func(parent, message, **kwargs)

        return method_argument_decorator

    @classmethod
    def websocket_function_arguments_decorator(cls, func):
        """
            Internal method not intended for users
        :param func:
        :return:
        """
        params = inspect.signature(func).parameters
        arg_keys = {}
        converter_keys= {}

        for name, param in params.items():  # type: inspect.Parameter
            if param.default is not inspect.Parameter.empty:
                if param.name in ["message"]:
                    raise TypeError(
                        f"Cannot use assign_args when using keyword arguments `message`: {param.name}")
                arg_keys[name] = param.default

                if param.annotation is not inspect.Parameter.empty:
                    converter_keys[name] = cls._eval_annotation(param.annotation, func)


        @functools.wraps(func)
        def argument_decorator(message: MessageHandler):
            kwargs = {}

            for name, default in arg_keys.items():
                kwargs[name] = message.args(name, default=default) #TODO also use annotation for type-casting
                if name in converter_keys:
                    try:
                        kwargs[name] = converter_keys[name](kwargs[name])
                    except (TypeError, ValueError,):
                        log.error(
                            "assign_args failed to use {converter!r} on {value!r}",
                            converter=converter_keys[name],
                            value=kwargs[name])

                        kwargs[name] = default

            return func(message, **kwargs)

        return argument_decorator


    def ws_expose(self, func: callable = None, assign_args=False):
        """
        See ws_class for use
        :param func:
        :param assign_args:
        :return:
        """

        if func is None and assign_args is True:
            def processor(real_func):
                setattr(real_func, self.WS_EXPOSED_FUNC, True)
                magic_func = self.websocket_class_arguments_decorator(real_func)
                return magic_func
            return processor

        else:
            setattr(func, self.WS_EXPOSED_FUNC, True)
            return func


class ApplicationRoutingHelperMixin:
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

    def add_class(self, route_str:str, **kwargs: ArbitraryKWArguments) -> CallableToResourceDecorator:
        """

        example usage
        ```
        @app.add_class("/my_foo")
        class Foo:
            @app.expose("/bar")
            def some_endpoint(self, request):
                ...

        ```
        would connect an instance of Foo and it's method `some_endpoint` to the url `/my_foo/bar`


        :param route_str:
        :param kwargs:
        :return:
        """
        return self.router.add(route_str, **kwargs)


    @staticmethod
    def expose(route_str, **kwargs):
        """
            Refer to add_class for usage
        :param route_str:
        :param kwargs:
        :return:
        """

        return expose_method(route_str, **kwargs)

    @staticmethod
    def set_view_prefilter(func):
        """
            Experimental, sets a view class method to be called before any `expose`'d method.
        :param func:
        :return:
        """
        return set_prefilter(func)

    @staticmethod
    def set_view_postfilter(func):
        """
            Experimental, sets a view class method to be called after any `expose`'d method.
        :param func:
        :return:
        """
        return set_postfilter(func)


    def add_resource(self, route_str:str, resource, **kwargs):
        """
        Add's a native/vanilla twisted.web.Resource object to the provided route_str

        :param route_str:
        :param resource:
        :param kwargs:
        :return:
        """
        return self.router.add_resource(route_str, thing=resource, route_kwargs=kwargs )


    def add_file(self, route_str: str, filePath: str, defaultType="text/html") -> File:
        """
        Just a simple helper for a common task of serving individual files

        :param route_str: A valid URI route string
        :param filepath: An absolute or relative path to a file to be served over HTTP
        :param default_type: What content type should a file be served as
        :return: twisted.web.static.File
        """

        assert Path(filePath).exists()
        file_resource = File(filePath, defaultType=defaultType)
        return self.router.add(route_str)(file_resource)


    def add_staticdir2(self, route_str: str, dirPath: T.Union[str, Path]) -> File:
        """
        TODO - remove calls to `add_staticdir2` and just use `add_staticdir`
        :param route_str:
        :param dirPath:
        :param recurse:
        :return:
        """

        if route_str.endswith("/") is False:
            route_str += "/"

        directory_resource = File(dirPath)

        self.router.add_directory(route_str, directory_resource)

        return directory_resource

    add_staticdir = add_staticdir2





class ApplicationErrorHandlingMixin:
    """
    The Error processing and handling aspect of Application

    """


    error_handlers: T.Dict[str, ErrorHandler]
    default_handler_cls:BaseHandler = DefaultHandler
    enable_debug: bool
    site: WebSite

    def __init__(self, enable_debug: bool =False):
        """
        :param enable_debug: Flag to decide if to use debugging tools
        """
        self.enable_debug = enable_debug

        self.error_handlers = dict(default=self.default_handler_cls(self))
        self.site.setErrorHandler(self.processingFailed)


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

    def add_error_handler(self, handler: T.Callable, error_type: T.Union[HTTPCode, int, Exception, str], override=False):
        """
        TODO cull this out or justify it's existence.

        Used similar to @handle_error but instead the first argument is a callable/reference to a function.
        :param handler:
        :param error_type:
        :param override:
        :return:
        """

        if error_type in self.error_handlers and override is False:
            old_func = self.error_handlers[error_type]
            raise ValueError(f"handle_error called twice to handle {error_type} with old {old_func} vs {handler}")

        self.error_handlers[error_type] = handler

    def processingFailed(self, request:StrRequest, reason: failure.Failure):
        """
        Internal method

        Called as part of the pipeline started when an exception occurs at Request.render and bubbles its
        way up to this part.


        :param request:
        :param reason:
        :return:
        """

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

            default_handler(request, reason)

        request.ensureFinished()

        return True






class Application(ApplicationRoutingHelperMixin, ApplicationErrorHandlingMixin, ApplicationWebsocketMixin):
    """
        Grand unified god module of txweb.

        TODO rename to TXWeb versus application to avoid confusion.
    """

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
        ApplicationErrorHandlingMixin.__init__(self, enable_debug=enable_debug)


        #Hooks
        self._before_render_handlers = []
        self._after_render_handlers = []

        self.__post_init__()


    def __post_init__(self) -> None:
        """
        Just a stub to make it easier for subclasses that don't want to mess with
          overloading __init__.

        :return:
        """


    @staticmethod
    def request_factory_partial(app: Application, request_kls: StrRequest):
        """
            A hack to intercept when a new http Request is created deep inside of twisted.web's protocol factory

        """

        def partial(*args, **kwargs):
            # pylint: disable=W0212
            request = request_kls(*args, **kwargs)
            request.add_before_render(app._call_before_render)
            request.add_after_render(app._call_after_render)
            request.site = app.site
            return request

        return partial


    @property
    def router(self) -> RoutingResource:
        """
        Provide access to the routing resource object.
        :return:
        """
        return self._router

    @property
    def site(self) -> WebSite:
        """
        Provides access to the server.Site instance
        :return:
        """
        return self._site

    @property
    def reactor(self) -> PosixReactorBase:
        """
        Provides access to the currently used reactor, used specifically to make testing easier.
        :return:
        """
        return self._reactor

    @reactor.setter
    def reactor(self, active_reactor: PosixReactorBase):
        self._reactor = active_reactor

    def listenTCP(self, port:int, interface:str= "127.0.0.1") -> Port:
        """
            Convenience helper which adds the HTTP protocol factory to the reactor and set it to listen to the provided
            interface and port
        """
        self._listening_port = self.reactor.listenTCP(port, self._site, interface=interface)
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
        """
        Internal method that iterates over all appended pre filter functions

        TODO - add logic to abort the loop if a post filter returns anything besides None

        :param request:
        :return:
        """
        # pylint: disable=W0703
        for func in self._before_render_handlers:
            try:
                func(request)
            except Exception:
                log.error(f"Before render failed {func}")

    def _call_after_render(self, request: StrRequest, body:T.Union[bytes,str,int]):
        """
            Internal method that iterates over all post filters.

        :param request:
        :param body:
        :return:
        """
        # pylint: disable=W0703
        for func in self._after_render_handlers:
            try:
                body = func(request, body)
            except Exception:
                log.error(f"After render failed {func}")

        return body



