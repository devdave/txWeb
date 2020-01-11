
from txweb.lib.str_request import StrRequest
from txweb.resources import SimpleFile
from txweb.errors import HTTP404, HTTP405

from twisted.web.resource import Resource

from pathlib import Path
import typing as T


class Directory(Resource):
    """
        TODO - This still needs a lot of work

        Non-recursive directory listing resource.  To clarify, this only serves the files in a given filepath and nothing
        in child directories nor their contents.

    """

    def __init__(self, path:T.Union[str, Path], recurse:bool=False):
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

    def handleGet(self, func):
        self._render_GET = func

        return func


    def show_files(self, func):
        self._render_GET = func
        return func

    def allowedFiles(self) -> T.List[str]:
        """
            Currently this mechanism is part of the basic security for Directory resource to ensure
            only the files in a given directory can be served and or listed.


        Returns:
            list: an explicit list of what files can be served from this Directory resource
        """
        return [file for file in self.path.glob("*") if file.exists() and file.is_file()]



    def getChild(self, path:bytes, request: StrRequest):

        path = path.decode("utf-8")
        if path.lower() in ["/", "", "index", "index.html"]:
            return self

        if path in [f.name for f in self.allowedFiles()]:
            return SimpleFile(self.path / path, defaultType="text/blah")


        raise HTTP404()


    def render(self, request):
        if request.method == b"GET":
            return self._render_GET(self, request, self.allowedFiles())

        elif request.method == b"HEAD":
            # TODO fix this up
            self._render_GET(self, request, self.allowedFiles())
            return b""
        else:
            raise HTTP405()

    @staticmethod
    def render_GET(parent, request, files):
        raise NotImplementedError("TODO")


    def __repr__(self):
        return f"<{self.__class__.__name__} at {id(self)!r} path={self.path!r}/>"

