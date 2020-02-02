"""
    Application is a common interface to Texas's various components

    The Application object logic has been broken apart into two mixin like classes and the main Application class.

    1. Routing logic (adding new routes/resources to the URL router) `ApplicationRoutingHelperMixin`
    2. Error handling `ApplicationErrorHandlingMixin`
    3. General utilities and resources ( website, router, reactor, etc) `Application`


"""
from __future__ import annotations
from .log import getLogger
log = getLogger(__name__)

from pathlib import Path
import typing as T

from twisted.internet.tcp import Port
from twisted.internet import reactor # type: PosixReactorBase
from twisted.python.compat import intToBytes
log.debug(f"Loaded reactor: {reactor!r}")

from .resources import RoutingResource, SimpleFile, Directory
from .lib import StrRequest, expose_method
from .web_views import WebSite
from .http_codes import HTTPCode
from .lib.errors.handler import DefaultHandler, DebugHandler, BaseHandler

from twisted.python import failure
from twisted.internet.posixbase import PosixReactorBase


if T.TYPE_CHECKING:


    ArbitraryListArg = T.NewType("ArbitraryListArg", T.List[T.Any])
    ArbitraryKWArguments = T.NewType("ArbitraryKWArguments", T.Optional[T.Dict[str, T.Any]])

    WebCallable = T.NewType("WebCallable", T.Callable[[StrRequest, ArbitraryListArg], T.Union[str, bytes]])
    CallableToResourceDecorator = T.NewType("CallableToResourceDecorator", T.Callable[[WebCallable], WebCallable])

    ErrorHandler = T.NewType("ErrorHandler", T.Callable[[StrRequest, failure.Failure], T.Union[bool, None]])



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

    def add_class(self, route_str:str, **kwargs: ArbitraryKWArguments) ->CallableToResourceDecorator:
        return self.router.add(route_str, **kwargs)

    def add_resource(self, route_str:str, resource, **kwargs):
        return self.router.add(route_str, **kwargs)(resource)

    def add_file(self, route_str: str, filePath: str, defaultType="text/html") -> SimpleFile:
        """
        Just a simple helper for a common task of serving individual files

        :param route_str: A valid URI route string
        :param filepath: An absolute or relative path to a file to be served over HTTP
        :param default_type: What content type should a file be served as
        :return: twisted.web.static.File
        """
        file_resource = SimpleFile(filePath, defaultType=defaultType)
        return self.router.add_resource(route_str, file_resource)

    def add_staticdir(self, route_str: str, dirPath: T.Union[str, Path]) -> Directory:

        if route_str.endswith("/") is False:
            route_str += "/"

        directory_resource = Directory(dirPath)

        self.router.add_directory(route_str, directory_resource)

        return directory_resource

    def expose(self, route_str, **kwargs):
        # TODO make route_str optional somehow
        return expose_method(route_str, **kwargs)


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
            default_handler(request, reason)

        request.ensureFinished()

        return True






class Application(ApplicationRoutingHelperMixin, ApplicationErrorHandlingMixin):
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

    def __init__(self,
                 namespace: str = None,
                 twisted_reactor: T.Optional[PosixReactorBase] = None,
                 request_factory:StrRequest=StrRequest,
                 enable_debug:bool=False
                 ):
        """

        """
        self._router = RoutingResource()
        self._site = WebSite(self._router, request_factory=Application.request_factory_partial(self, request_factory))
        self._router.site = self._site
        self._reactor = twisted_reactor or None  # type: PosixReactorBase

        self.name = namespace
        self._listening_port = None

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
    def reactor(self, reactor: PosixReactorBase):
        self._reactor = reactor

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
                log.exception(f"Before render failed {func}")

    def _call_after_render(self, request: StrRequest, body:T.Union[bytes,str,int]):
        for func in self._after_render_handlers:
            try:
                func(request)
            except Exception:
                log.exception(f"After render failed {func}")




