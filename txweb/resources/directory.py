
from txweb.util.str_request import StrRequest
from txweb.resources import SimpleFile
from twisted.web.resource import Resource

from pathlib import Path


class Directory(Resource):

    def __init__(self, path, recurse=False):
        """

        :param path: str/Path an ABSOLUTE filepath to a directory to be exposed to a http client
        :param recurse: bool should Directory exposed subdirectories
        """
        Resource.__init__(self)
        self.path = Path(path) #  type: Path
        self.isLeaf = False
        self.recurse = False

        #dynamic helpers

        self._render_GET = self.render_GET


    def show_files(self, func):
        self._render_GET = func
        return func

    def allowedFiles(self):
        return [file.name for file in self.path.glob("*") if file.exists() and file.is_file()]



    def getChild(self, path, request: StrRequest):

        if path == "/" or path == "":
            return self

        if path in self.allowedFiles():
            # TODO find mimetype
            return SimpleFile(self.path / path, defaultType="text/blah")


    def render(self, request):
        if request.method == b"GET":
            return self._render_GET(self, request, self.allowedFiles())

        elif request.method == b"HEAD":
            return self._render_GET(self, request, self.allowedFiles())
        else:
            raise ValueError(f"Unable to process {request.method!r}")


    def render_GET(request, files):
        raise NotImplementedError("TODO")