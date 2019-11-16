
from twisted.web.static import File as txFile
import pathlib


class File(txFile):

    def __init__(self, path, default_type='text/html', ignored_exts=(), registry=None, allow_ext=0):

        if pathlib.Path(path).exists() is False:
            raise ValueError(f"Unable to find {path}, file does not exist")

        txFile.__init__(self,
                        path,
                        defaultType=default_type,
                        ignoredExts=ignored_exts,
                        registry=registry,
                        allowExt=allow_ext)
