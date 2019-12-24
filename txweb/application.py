from __future__ import annotations
from .log import getLogger
log = getLogger(__name__)

from pathlib import Path
import typing as T

from twisted.internet.tcp import Port
from twisted.internet import reactor # type: PosixReactorBase
log.debug(f"Loaded reactor: {reactor!r}")

from .resources import RoutingResource, SimpleFile, Directory
from .lib import StrRequest, expose_method
from .web_views import WebSite
from .errors import HTTPCode


if T.TYPE_CHECKING:
    from twisted.python import failure
    from twisted.internet.posixbase import PosixReactorBase

    ArbitraryListArg = T.NewType("ArbitraryListArg", T.List[T.Any])
    ArbitraryKWArguments = T.NewType("ArbitraryKWArguments", T.Optional[T.Dict[str, T.Any]])

    WebCallable = T.NewType("WebCallable", T.Callable[[StrRequest, ArbitraryListArg], T.Union[str, bytes]])
    CallableToResourceDecorator = T.NewType("CallableToResourceDecorator", T.Callable[[WebCallable], WebCallable])

    ErrorHandler = T.NewType("ErrorHandler", T.Callable[[StrRequest, failure.Failure], bool])



class _ApplicationTemplateSupportMixin(object):
    def __init__(self):
        self.template_base = None

    def set_basedir(self, base_path:T.Union[Path, str]):
        self.template_base = base_path


class _ApplicationRoutingHelperMixin(object):
    """
        Assumes self.router provides a RoutingResource reference/object

        Proxies to RoutingResource to facilitate easier debugging
    """

    def add(self, route_str:str, **kwargs: ArbitraryKWArguments) -> CallableToResourceDecorator:
        return self.router.add(route_str, **kwargs)

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

class _ApplicationErrorHandlingMixin(object):

    def __init__(self, enable_debug: bool =False, **kwargs):
        """

        """
        self.error_handlers = {}
        self.enable_debug = enable_debug

        self.site.addErrorHandler(self.processingFailed)


    def default_error_handler(self, request: StrRequest, reason: failure.Failure)->bool:
        # Check if this is a HTTPCode error
        if isinstance(HTTPCode, reason.type) or issubclass(reason.type, HTTPCode):
            exc = reason.value  # type: HTTPCode
            request.setResponseCode(exc.code, exc.message)
        else:
            request.setResponseCode(500, b"Internal server error")
            log.debug(f"None HTTPCode error was caught: {reason.type} - {reason.value}")

        if self.enable_debug is True and request.method.lower() != b"head":
            #TODO return error resource
            pass
        else:
            pass

        request.write(f"Something bad happened with {reason!r}".encode("utf-8"))
        request.finish()
        return

    def handle_error(self, error_type: T.Union[HTTPCode, int, Exception]) -> T.Callable:

        def processor(func: ErrorHandler) -> ErrorHandler:
            if error_type in self.error_handlers:
                old_func = self.error_handlers[error_type]
                raise ValueError(f"handle_error called twice to handle {error_type} with old {old_func} vs {func}")

            self.error_handlers[error_type] = func
            return func

        return processor


    def processingFailed(self, request:StrRequest, reason: failure.Failure):


        if reason.type in self.error_handlers:
            return self.error_handlers[reason.type](request, reason)
        elif isinstance(reason.value, HTTPCode) and reason.value.code in self.error_handlers:
            return self.error_handlers[reason.value.code](request, reason)
        else:
            self.default_error_handler(request, reason)

        if request.finished != True:
            request.finish()

        return True






class Application(_ApplicationRoutingHelperMixin, _ApplicationErrorHandlingMixin):
    """
        Similar to Klein and its influence Flask, the goal is to consolidate
        technical debt into one God module antipattern class.

        Purposes:
            Provides a public API to Site, HTTPErrors, RoutingResource, and additional helpers.
    """

    def __init__(self,
                 twisted_reactor: PosixReactorBase = None,
                 namespace:str=None,
                 request_factory:StrRequest=StrRequest,
                 enable_debug:bool=False                 ):
        """
        @param twisted_reactor: Intended for debugging purposes
        @param namespace: placeholder intended for debugging
        @param request_factory: Used by Website(twisted.web.server.Site), for debugging purposes
        @param debug: Placeholder to enable extended debugging
        """
        self._router = RoutingResource()
        self._site = WebSite(self._router, request_factory=Application.request_factory_partial)
        self._router.site = self._site
        self._reactor = twisted_reactor or None  # type: PosixReactorBase

        self.name = namespace
        self._listening_port = None

        _ApplicationRoutingHelperMixin.__init__(self)
        # _ApplicationTemplateSupportMixin.__init__(self)
        _ApplicationErrorHandlingMixin.__init__(self, enable_debug=enable_debug)





        #Hooks
        self._before_render_handlers = []
        self._after_render_handlers = []


    @staticmethod
    def request_factory_partial(app:'Application', request_kls:StrRequest):

        def partial(*args, **kwargs):
            request = request_kls(*args, **kwargs)
            request.add_before_render(app._call_before_render)
            request.add_after_render(app._call_after_render)
            request.site = app.site
            return request

        return partial


    def __call__(self, namespace):
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

    def listenTCP(self, port, interface= "127.0.0.1") -> Port:
         self._listening_port = self.reactor.listenTCP(port, self.site, interface=interface)
         return self._listening_port

    def before_render(self, func: T.Callable[[StrRequest], None]):
        self._before_render_handlers.append(func)
        return func

    def after_render(self, func: T.Callable[[StrRequest], None]):
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




