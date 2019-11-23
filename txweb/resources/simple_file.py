from txweb.util.str_request import StrRequest

from twisted.web.static import File, getTypeAndEncoding
from twisted.web.server import NOT_DONE_YET
from twisted.web import http

from twisted.python import log

import errno
from pathlib import Path
import typing as T


class SimpleFile(File):
    """
    Duplicates tx.web.static.File but splits it apart
        from serving dual purposes of being a Resource Branch and a leaf.

    Purpose: Serve only a specific file

    Research:
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Range
    https://tools.ietf.org/html/rfc7233#section-4.2

    """
    isLeaf = True # type: T.Union[bool, int]

    def __init__(self, path:T.Union[str, Path], defaultType = "text/plain"):

        if False in [Path(path).is_file(), Path(path).exists()]:
            raise ValueError(f"{self.path} is not a file and or does not exist")

        File.__init__(self, str(path), defaultType=defaultType)

        self.isLeaf = True

    def render(self, request:StrRequest):
        if request.method.lower() == "get":
            return self.render_GET(request)
        elif request.method.lower() == "head":
            return self.render_HEAD(request)
        else:
            log.err(request.method, "SimpleFile.render was given a bad HTTP method")
            raise RuntimeError(f"{request.method} is not available for this resource")


    def render_GET(self, request:StrRequest):

        request.setHeader("accept-ranges", "bytes")

        if self.type is None:
            self.type, self.encoding = getTypeAndEncoding(self.basename(),
                                                          self.contentTypes,
                                                          self.contentEncodings,
                                                          self.defaultType)

        try:
            fileForReading = self.openForReading()
        except IOError as exc:
            if exc.erno == errno.EACCESS:
                # TODO Replace with a 500 exception
                raise RuntimeError(f"Unable to read {self.path!r} due to permission error.")

        if request.setLastModified(self.getModificationTime()) is http.CACHED:
            # TODO research
            return b""

        producer = self.makeProducer(request, fileForReading)
        producer.start()

        return NOT_DONE_YET


    def render_HEAD(self, request:StrRequest):
        self._setContentHeaders(request)
        return b""