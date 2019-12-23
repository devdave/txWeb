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
from twisted.web import resource
from twisted.web import http
# noinspection PyProtectedMember
from twisted.web.http import _parseHeader
# noinspection PyProtectedMember
from twisted.python.compat import _PY3, _PY37PLUS, nativeString, escape, intToBytes

from werkzeug.formparser import FormDataParser

import cgi
import json
from urllib.parse import parse_qs
import typing as T

if T.TYPE_CHECKING:
from ..log import getLogger

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

    def writeJSON(self, data:T.Dict):
        """
            Utility to take a dictionary and convert it to a JSON string
        """
        return self.write(json.dumps(data))

    def setHeader(self, name, value):
        # TODO check if this is redundant
        if isinstance(name, str):
            name = name.encode("utf-8")

        if isinstance(value, str):
            value = value.encode("utf-8")

        return Request.setHeader(self, name, value)

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
            body = resrc.render(self)
        except UnsupportedMethod as e:
            allowedMethods = e.allowedMethods
            if (self.method == b"HEAD") and (b"GET" in allowedMethods):
                # We must support HEAD (RFC 2616, 5.1.1).  If the
                # resource doesn't, fake it by giving the resource
                # a 'GET' request and then return only the headers,
                # not the body.
                self._log.info(
                    "Using GET to fake a HEAD request for {resrc}",
                    resrc=resrc
                )
                self.method = b"GET"
                self._inFakeHead = True
                body = resrc.render(self)

                if body is NOT_DONE_YET:
                    self._log.info(
                        "Tried to fake a HEAD request for {resrc}, but "
                        "it got away from me.", resrc=resrc
                    )
                    # Oh well, I guess we won't include the content length.
                else:
                    self.setHeader(b'content-length', intToBytes(len(body)))

                self._inFakeHead = False
                self.method = b"HEAD"
                self.write(b'')
                self.finish()
                return

            if self.method in (supportedMethods):
                # We MUST include an Allow header
                # (RFC 2616, 10.4.6 and 14.7)
                self.setHeader(b'Allow', b', '.join(allowedMethods))
                s = ('''Your browser approached me (at %(URI)s) with'''
                     ''' the method "%(method)s".  I only allow'''
                     ''' the method%(plural)s %(allowed)s here.''' % {
                         'URI': escape(nativeString(self.uri)),
                         'method': nativeString(self.method),
                         'plural': ((len(allowedMethods) > 1) and 's') or '',
                         'allowed': ', '.join(
                            [nativeString(x) for x in allowedMethods])
                     })
                epage = resource.ErrorPage(http.NOT_ALLOWED,
                                           "Method Not Allowed", s)
                body = epage.render(self)
            else:
                epage = resource.ErrorPage(
                    http.NOT_IMPLEMENTED, "Huh?",
                    "I don't know how to treat a %s request." %
                    (escape(self.method.decode("charmap")),))
                body = epage.render(self)
        # end except UnsupportedMethod

        if body is NOT_DONE_YET:
            return
        if not isinstance(body, bytes):
            body = resource.ErrorPage(
                http.INTERNAL_SERVER_ERROR,
                "Request did not return bytes",
                "Request: " + util._PRE(reflect.safe_repr(self)) + "<br />" +
                "Resource: " + util._PRE(reflect.safe_repr(resrc)) + "<br />" +
                "Value: " + util._PRE(reflect.safe_repr(body))).render(self)

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

    def _processFormData(self, ctype, clength):
        """
        Processes POST requests and puts POST'd arguments into args.

        Thank you Cristina - http://www.cristinagreen.com/uploading-files-using-twisted-web.html

        TODO this can be problematic if a binary file is being uploaded
        """
        options = {}


        ctype = ctype.decode("utf-8")  # type: str
        if ";" in ctype:
            """
                TODO Possible need to replace some of the header processing logic as boundary part of content-type 
                leaks through.
            """
            ctype, boundary = ctype.split(";", 1)
            if "=" in boundary:
                _, boundary = boundary.split("=", 1)

            options['boundary'] = boundary


        clength = int(clength)

        self.content.seek(0,0)
        parser = FormDataParser()
        _, self.form, self.files = parser.parse(self.content, ctype, clength, options=options)
        self.content.seek(0,0)

        # mfd = b'multipart/form-data'
        # key, pdict = _parseHeader(ctype)
        # pdict["CONTENT-LENGTH"] = clength
        #
        # if key == b'application/x-www-form-urlencoded':
        #     self.form.update(parse_qs(self.content.read(), 1))
        # elif key == mfd:
        #     try:
        #         if _PY37PLUS:
        #             cgi_args = cgi.parse_multipart(
        #                 self.content, pdict,
        #                 errors="surrogateescape")
        #         else:
        #             cgi_args = cgi.parse_multipart(self.content, pdict)
        #
        #         if not _PY37PLUS and _PY3:
        #             self.form.update({x.encode('iso-8859-1'): y for x, y in cgi_args.items()})
        #         elif _PY37PLUS:
        #             # The parse_multipart function on Python 3.7+
        #             # decodes the header bytes as iso-8859-1 and
        #             # decodes the body bytes as utf8 with
        #             # surrogateescape -- we want bytes
        #             self.form.update({
        #                 x.encode('iso-8859-1'):
        #                     [z.encode('utf8', "surrogateescape")
        #                      if isinstance(z, str) else z for z in y]
        #                 for x, y in cgi_args.items()})
        #             pass
        #
        #         else:
        #             self.form.update(cgi_args)
        #     except Exception as e:
        #         # It was a bad request, or we got a signal.
        #         # noinspection PyProtectedMember
        #         self.channel._respondToBadRequestAndDisconnect()
        #         if isinstance(e, (TypeError, ValueError, KeyError)):
        #             return
        #         else:
        #             # If it's not a userspace error from CGI, reraise
        #             raise


    def processingFailed(self, reason):
        self.site.processingFailed(self, reason)

    @property
    def json(self):
        if self.getHeader("Content-Type") not in ["application/json", "text/json"]:
            raise RuntimeError(
                "Request content-type is not JSON content type "
                f"{self.getHeader('Content-Type')!r}")

        return json.loads(self.content.read())
