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


from twisted.web.server import Request
# noinspection PyProtectedMember
from twisted.web.http import _parseHeader
# noinspection PyProtectedMember
from twisted.python.compat import _PY3, _PY37PLUS

import cgi
import json
from urllib.parse import parse_qs


class StrRequest(Request):

    def write(self, data):

        if isinstance(data, str):
            data = data.encode("utf-8")
        elif isinstance(data, bytes):
            pass
        else:
            raise ValueError(f"Attempting to write to transport {type(data)}-{data!r}"
                             " must be ByteString or Str")

        return Request.write(self, data)

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

        # Thank you Cristina - http://www.cristinagreen.com/uploading-files-using-twisted-web.html

        self.content.seek(0, 0)

        self.args = {}

        self.method, self.uri = command, path
        self.clientproto = version

        x = self.uri.split(b"?", 1)

        if len(x) == 1:
            self.path = self.uri
        else:
            self.path, arg_string = x
            self.args = parse_qs(arg_string.decode())

        args = self.args
        ctype = self.requestHeaders.getRawHeaders(b'content-type')
        clength = self.requestHeaders.getRawHeaders(b'content-length')
        if ctype is not None:
            ctype = ctype[0]

        if clength is not None:
            clength = clength[0]

        if self.method == b"POST" and ctype and clength:
            mfd = b'multipart/form-data'
            key, pdict = _parseHeader(ctype)
            pdict["CONTENT-LENGTH"] = clength

            if key == b'application/x-www-form-urlencoded':
                args.update(parse_qs(self.content.read(), 1))
            elif key == mfd:
                try:
                    if _PY37PLUS:
                        cgi_args = cgi.parse_multipart(
                            self.content, pdict, encoding='utf8',
                            errors="surrogateescape")
                    else:
                        cgi_args = cgi.parse_multipart(self.content, pdict)

                    if not _PY37PLUS and _PY3:
                        # The parse_multipart function on Python 3
                        # decodes the header bytes as iso-8859-1 and
                        # returns a str key -- we want bytes so encode
                        # it back
                        self.args.update({x.encode('iso-8859-1'): y
                                          for x, y in cgi_args.items()})
                    elif _PY37PLUS:
                        # The parse_multipart function on Python 3.7+
                        # decodes the header bytes as iso-8859-1 and
                        # decodes the body bytes as utf8 with
                        # surrogateescape -- we want bytes
                        self.args.update({
                            x.encode('iso-8859-1'):
                                [z.encode('utf8', "surrogateescape")
                                 if isinstance(z, str) else z for z in y]
                            for x, y in cgi_args.items()})

                    else:
                        self.args.update(cgi_args)
                except Exception as e:
                    # It was a bad request, or we got a signal.
                    # noinspection PyProtectedMember
                    self.channel._respondToBadRequestAndDisconnect()
                    if isinstance(e, (TypeError, ValueError, KeyError)):
                        return
                    else:
                        # If it's not a userspace error from CGI, reraise
                        raise

            self.content.seek(0, 0)

        self.process()

    @property
    def json(self):
        if self.getHeader("Content-Type") not in ["application/json", "text/json"]:
            raise RuntimeError(
                "Request content-type is not JSON content type "
                f"{self.getHeader('Content-Type')!r}")

        return json.loads(self.content.read())
