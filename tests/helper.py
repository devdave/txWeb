

import unittest

from twisted.web.test.test_web import DummyRequest

class Helper(unittest.TestCase):
    def runTest(self):
        pass

helper = Helper()





ensureBytes = lambda x: x if isinstance(x, bytes) else x.encode()


class MockRequest(DummyRequest):# prama: no cover
    """
        Utility class that builds on DummyRequest to fullfill some missing methods
    """
    def __init__(self, postpath = [], path = "/", args = {}):
        DummyRequest.__init__(self, postpath)
        self.path = ensureBytes(path)
        self.postpath = self.path.split(b"/")
        self.prepath = []

        self.redirectToURL = None
        for name, arg in args.items():
            self.addArg(name, arg)


    def redirect(self, url):
        """
            Just a simple trap to catch if .redirect was called and what the URL is
        """
        self.redirectToURL = url

    def isSecure(self):
        return False
