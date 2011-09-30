
from twisted.web.test.test_web import DummyRequest



class TestRequest(DummyRequest):# prama: no cover
    """
        Utility class that builds on DummyRequest to fullfill some missing methods
    """
    def __init__(self, postpath = [], path = "/", args = {}):
        DummyRequest.__init__(self, postpath)
        self.path = path
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