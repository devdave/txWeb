
from twisted.web.test.test_web import DummyRequest
from twisted.web.http_headers import Headers
from twisted.web.server import Session


class TestRequest(DummyRequest):
    """
        A borderline mock of a real web Request object.

        As I've understood session, they're memory resident and not persistent
         which is fine as storing to file or service ( redis/memcache ) would
         be problematic as request.getSession() would need to be engineered
         in such a way to return a deferred... which is tedious.


    """

    def __init__(self, postpath, path = "/", session=None, args = {}):
        self.path = path
        self.redirectToURL = None
        self.sitepath = []
        self.written = []
        self.finished = 0
        self.postpath = postpath
        self.prepath = []
        self.session = None
        #OLD self.protoSession = session or Session(0, self)
        #TODO, argument #1 is titled site, figure out what Session needs it for
        # and duplicate behavior
        for name, arg in args.items():
            self.addArg(name, arg)

        self.protoSession = session or Session(self, uid = 0)
        self.outgoingHeaders = {}
        self.responseHeaders = Headers()
        self.responseCode = None
        self.headers = {}
        self._finishedDeferreds = []

    def getSession(self, interface = None):
        session = DummyRequest.getSession(self)
        if interface:
            return self.session.getComponent(interface)

        return self.session

    def redirect(self, url):
        """
            Just a simple trap to catch if .redirect was called and what the URL is
        """
        self.redirectToURL = url


    def isSecure(self):
        return False