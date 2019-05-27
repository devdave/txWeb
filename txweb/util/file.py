
from twisted.web.static import File as txFile
import pathlib


class File(txFile):

    def __init__(self, path, defaultType='text/html', ignoredExts=(), registry=None, allowExt=0):

        if pathlib.Path(path).exists() is False:
            raise ValueError(f"Unable to find {path}, file does not exist")

        txFile.__init__(self, path, defaultType='text/html', ignoredExts=(), registry=None, allowExt=0)