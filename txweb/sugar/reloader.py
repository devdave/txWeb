"""
    Copied from WebMud framework, will need to check license though not too important
    as I own that project also... I mean I am not going to sue myself, right?  Especially
    as this is some fairly trivial stuff here and I don't even know if it will
    work correctly with txweb proper.
"""
#pragma: no cover
from twisted.python.rebuild import rebuild
from twisted.internet import reactor
from os.path import exists, isdir, dirname, abspath
from os import stat
from stat import ST_MTIME
import sys

class ModuleReloader(object): #pragma: no cover
    """
        A development tool that dynamically reloads code def's IN PLACE.

        This has some not so inconsequential consequences, specifically if you
        modify how a class is initialized ( changes to self.vars ) it might have
        some profoundly weird side-effects.

        On the flip side, if you're changing business logic for a specific method
        or bit of code, it can dramatically speed up development without having
        to repeatedly
    """

    @classmethod
    def WatchThis(cls, path):
        """
            Adds reload monitors all source files for a given directory

            :param path: a Valid file or directory to be watched
        """
        if not isdir(path):
            dirpath = dirname(path)
            if not dirpath:
                dirpath = dirname(abspath(path))
                if not dirpath:
                    raise ValueError("Unsure how to monitor %s" % path)
            path = dirpath

        targets = []
        for name, module in sys.modules.items():
            if name == "__main__":
                continue
            if module:
                modpath = getattr(module, "__file__", "")
                if modpath:
                    moddir = dirname(abspath(modpath))
                    if moddir.startswith(path):
                        targets.append(module)


        return cls(targets)

    def __init__(self, watchlist = [] ):
        self.watchlist = {}
        for module in watchlist:
            fileName = module.__file__
            if fileName.endswith(".pyc"):
                fileName = fileName[:-1]
            assert exists(fileName)
            self.watchlist[module] = (fileName ,  stat(fileName)[ST_MTIME])
        reactor.callLater(10, self)


    def __call__(self):
        try:
            for module, (file, ts) in self.watchlist.items():
                newTS = stat(file)[ST_MTIME]
                if ts != newTS:
                    self.watchlist[module] = (file ,  newTS)
                    rebuild(module)
                    print "Reloaded %s " % module
        finally:
            reactor.callLater(10, self)