"""
    STATUS PENDING

    Redo web Request to act as a str<->bytes proxy between our
    application and twisted library.

    Since Py3, all strings are unicode which is problematic for twisted as it
    only works with bytes (and to some extent ascii).   Instead of rewriting the entire library
    and bedazzling it with flaky string encode/decode logic, the twisted maintainers
    enforced bytes (or gtfo) only.

    In this case, I am making a proxy request to catch str and convert to bytes before it moves upward
    and into the twisted library.   Unfortunately this is a doozy of a sub-project as its not just Request but also
    headers logic.
"""
from twisted.python import reflect
from twisted.web.error import UnsupportedMethod
from twisted.web.server import Request, NOT_DONE_YET, supportedMethods
from twisted.web.http import FOUND
from twisted.web import resource
from twisted.web import http
# noinspection PyProtectedMember
from twisted.web.http import _parseHeader
# noinspection PyProtectedMember
from twisted.python.compat import _PY3, _PY37PLUS, nativeString, escape, intToBytes

from werkzeug.formparser import FormDataParser
from werkzeug import MultiDict

import cgi
import json
from urllib.parse import parse_qs
import typing as T

from ..log import getLogger
from ..http_codes import HTTP500

log = getLogger(__name__)

if T.TYPE_CHECKING: # pragma: no cover
    from werkzeug import FileStorage


class StrRequest(Request):

    NOT_DONE_YET: T.Union[int, bool]  = NOT_DONE_YET

    def __init__(self, *args, **kwargs):

        Request.__init__(self, *args, **kwargs)

        # self.args = {} is already defined in Request's init
        self.form = {}   # type: T.Dict[str, str]
        self.files = {}  # type: T.Dict[str, FileStorage]

        self._call_before_render = None
        self._call_after_render = None


    def add_before_render(self, func):
        self._call_before_render = func
        return func


    def add_after_render(self, func):
        self._call_after_render = func
        return func


    def write(self, data:T.Union[bytes, str]):

        if isinstance(data, str):
            data = data.encode("utf-8")
        elif isinstance(data, bytes):
            pass
        else:
            raise ValueError(f"Attempting to write to transport {type(data)}-{data!r}"
                             " must be bytes or Str")

        return Request.write(self, data)

    def writeTotal(self, response_body:T.Union[bytes, str], code:T.Union[int, str, bytes] = None,
                   message:T.Union[bytes, str]=None) -> T.NoReturn:
        """
        
        :param response_body: Content intended for after headers 
        :param code: Optional HTTP Code to use
        :param message: Optional HTTP response message to use
        :return: 
        """

        content_length = intToBytes(len(response_body))
        self.setHeader("Content-Length", content_length)

        if code is not None:
            self.setResponseCode(code, message=message)

        self.write(response_body)
        self.ensureFinished()




    def writeJSON(self, data:T.Dict):
        """
            Utility to take a dictionary and convert it to a JSON string
        """
        return self.write(json.dumps(data))

    def setHeader(self, name:T.Union[str, bytes], value:T.Union[str, bytes]):
        """
            A quick wrapper to convert unicode inputs to utf-8 bytes

            Arguments:
                name: A valid HTTP header
                value: Syntactically correct value for the header name
        """
        if isinstance(name, str):
            name = name.encode("utf-8")

        if isinstance(value, str):
            value = value.encode("utf-8")

        return Request.setHeader(self, name, value)

    def setResponseCode(self, code:int=500, message:T.Optional[T.Union[str,bytes]]=b"Failure processing request"):
        if message and not isinstance(message,bytes):
            message = message.encode("utf-8")

        return Request.setResponseCode(self, code, message)

    def ensureFinished(self):
        if self.finished not in [1, True]:
            self.finish()

    def requestReceived(self, command, path, version):
        """
            Looks for POST'd arguments in form format (eg multipart).
            Allows for file uploads and adds them to .args

            TODO add a files attribute to StrRequest?
        """
        self.content.seek(0, 0)

        self.args = {}
        self.form = {}

        self.method, self.uri = command, path
        self.clientproto = version

        x = self.uri.split(b"?", 1)

        if len(x) == 1:
            self.path = self.uri
        else:
            self.path, arg_string = x
            self.args = parse_qs(arg_string.decode())

        ctype = self.requestHeaders.getRawHeaders(b'content-type')
        clength = self.requestHeaders.getRawHeaders(b'content-length')
        if ctype is not None:
            ctype = ctype[0]

        if clength is not None:
            clength = clength[0]

        if self.method == b"POST" and ctype and clength:
            self._processFormData(ctype,  clength)

            self.content.seek(0, 0)

        # Args are going to userland, switch bytes back to str
        query_args = self.args.copy()

        def query_iter(arguments):
            for key, values in arguments.items():
                key = key.decode("utf-8") if isinstance(key, bytes) else key
                for val in values:
                    val = val.decode("utf-8") if isinstance(val, bytes) else val
                    yield (key, val,)

        self.args = MultiDict(list(query_iter(query_args)))

        self.process()

    def render(self, resrc):
        """
        Ask a resource to render itself.

        If the resource does not support the requested method,
        generate a C{NOT IMPLEMENTED} or C{NOT ALLOWED} response.

        @param resrc: The resource to render.
        @type resrc: L{twisted.web.resource.IResource}

        @see: L{IResource.render()<twisted.web.resource.IResource.render()>}
        """
        try:
            if self._call_before_render is not None:
                self._call_before_render(self)
            body = resrc.render(self)
            if self._call_after_render is not None:
                self._call_after_render(self, body)
        except:
            #log.exception(f"While processing {self.method!r} {self.uri}")
            raise

        # TODO deal with HEAD requests or leave it to the Application developer to deal with?

        if body is NOT_DONE_YET:  #TODO replace NOT_DONE_YET with a sentinel versus integer
            return

        if not isinstance(body, bytes):
            log.error(f"<{type(resrc)} {resrc}> - uri={self.uri} returned {type(body)}:{len(body)} but MUST return a byte string")
            raise HTTP500()

        if self.method == b"HEAD":
            if len(body) > 0:
                # This is a Bad Thing (RFC 2616, 9.4)
                self._log.info(
                    "Warning: HEAD request {slf} for resource {resrc} is"
                    " returning a message body. I think I'll eat it.",
                    slf=self,
                    resrc=resrc
                )
                self.setHeader(b'content-length',
                               intToBytes(len(body)))
            self.write(b'')
        else:
            self.setHeader(b'content-length',
                           intToBytes(len(body)))
            self.write(body)
        self.finish()

    def _processFormData(self, content_type, content_length):
        """
        Processes POST requests and puts POST'd arguments into args.

        Thank you Cristina - http://www.cristinagreen.com/uploading-files-using-twisted-web.html

        TODO this can be problematic if a binary file is being uploaded
        TODO verify Twisted HTTP channel/transport blows up if file upload size is "too big"
        """
        options = {}


        if isinstance(content_type, bytes):
            content_type = content_type.decode("utf-8")  # type: str


        if ";" in content_type:
            """
                TODO Possible need to replace some of the header processing logic as boundary part of content-type 
                leaks through.
                eg "Content-type": "some/mime_type;boundary=----BLAH"
            """
            content_type, boundary = content_type.split(";", 1)
            if "=" in boundary:
                _, boundary = boundary.split("=", 1)

            options['boundary'] = boundary

        content_length = int(content_length)

        self.content.seek(0,0)
        parser = FormDataParser()
        _, self.form, self.files = parser.parse(self.content, content_type, content_length, options=options)
        self.content.seek(0, 0)

    def processingFailed(self, reason):
        self.site.processingFailed(self, reason)

    @property
    def json(self):
        if self.getHeader("Content-Type") not in ["application/json", "text/json"]:
            raise RuntimeError(
                "Request content-type is not JSON content type "
                f"{self.getHeader('Content-Type')!r}")

        return json.loads(self.content.read())

    def redirect(self, url, code = FOUND):
        """
        Utility function that does a redirect.

        Set the response code to L{FOUND} and the I{Location} header to the
        given URL.

        The request should have C{finish()} called after this.

        @param url: I{Location} header value.
        @type url: L{bytes} or L{str}
        """
        self.setResponseCode(code)
        self.setHeader(b"location", url)
