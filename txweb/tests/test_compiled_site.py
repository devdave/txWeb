#pragma: no cover
from os.path import dirname, abspath, join
import nose
from nose.tools import eq_

from pprint import pprint

from txweb.core import CSite
from txweb.util import expose
from txweb.util.testing import TestRequest

from twisted.web.test.test_web import DummyRequest
from twisted.web.resource import ErrorPage
from twisted.web.resource import NoResource
from twisted.web.static import File
from twisted.web.server import NOT_DONE_YET
from twisted.web.static import DirectoryLister

relPath = lambda filename : abspath(join(dirname(__file__), ".." , filename))

class NearPage(object): #pragma: no cover
    @expose
    def test(self, request):
        return True

class FarPage(object): #pragma: no cover
    @expose
    def is_here(self, request):
        return True

class SubPage(object): #pragma: no cover
    @expose
    def foo(self, request):
        return True

    @expose
    def bar(self, request): #pragma: no cover
        return True

    @expose
    def __default__(self, request): #pragma: no cover
        return True

    far = FarPage()

class Root(object):#pragma: no cover

    @expose
    def index(self, request):
        return True

    @expose
    def spaced_named(self, request):
        return True

    @expose
    def __default__(self, request):
        return True

    near = NearPage()
    sub = SubPage()

    #Using 418 as nothing should ever use it
    deadend = ErrorPage(418, "I'm a teapot!", "This node is not the node you're looking for!")



class RootWithStaticIndex(object):
    index = File(relPath("LICENSE.txt"))

class RootWithStaticDirectory(object):

    files = File(relPath("tests/test_data/"))



def make_new_graph():
    root = Root()
    return CSite(root)


def test_compiles():
    make_new_graph()

def test_graph_is_correct():
    root = make_new_graph()
    pprint(root.object_graph.keys(), indent = 2)
    expected_routes = [ '/',
                        '/deadend',
                        '/index',
                        '/near/test',
                        '/spaced_named',
                        '/sub/bar',
                        '/sub/far/is_here',
                        '/sub/foo']

    eq_(len(root.object_graph), 8)
    for test_path in expected_routes:
        found = False
        for url_test, action in root.object_graph.items():
            if url_test.match(test_path):
                found = True
                break

        assert found, "Failed to find %s" % test_path

def test_site_routeRequest_HandlesDirectoryListing():

    staticDir = CSite(RootWithStaticDirectory())
    request = TestRequest([], "/files/")

    action = staticDir.routeRequest(request)

    response = action.render(request)
    assert isinstance(action, DirectoryLister)

def test_site_routeRequest_CorrectlyRoutesToAChildOfstaticFileResource():
    staticDir = CSite(RootWithStaticDirectory())
    request = TestRequest([], "/files/a.txt")

    action = staticDir.routeRequest(request)
    response = action.render(request)
    assert not isinstance(action, DirectoryLister)
    assert response == NOT_DONE_YET
    assert request.written[0].count("a") > 0

def test_site_routeRequest_CorrectlyHandlesSubDirectories():
    staticDir = CSite(RootWithStaticDirectory())

    request = TestRequest([], "/files/subdir/b.txt")

    #from dbgp.client import brk; brk("192.168.1.2", 9090)
    action = staticDir.routeRequest(request)
    response = action.render(request)
    assert not isinstance(action, DirectoryLister)
    assert response == NOT_DONE_YET
    assert request.written[0].count("b") > 0




def test_site_routRequest_HandlesIndexAsResource():
    staticSite = CSite(RootWithStaticIndex())

    request = TestRequest([], "/")

    action = staticSite.routeRequest(request)
    response = action.render(request)
    assert response == NOT_DONE_YET
    with open(relPath("LICENSE.txt")) as testFile:
        expected = testFile.read()
        assert len(request.written) ==  1, "Expected written log to be equal to one"
        actualSize = len(request.written[0])
        expectedSize = len(expected)
        actual = request.written[0]
        assert expectedSize == actualSize, "Expected size doesn't match actual"
        assert expected == actual, "Expecting actual written body to equal expected body"

def test_site_routeRequest_HandlesErrorPageResource():

    request = TestRequest([], "/deadend")

    action = make_new_graph().routeRequest(request)
    assert action.code == 418, "Expecting tea pot, but got %s" % action.code
    assert isinstance(action, ErrorPage)

def test_site_routeRequestCorrectly():
    u2m = {}
    site = make_new_graph()
    root = site.resource

    u2m["/"] = root.index
    u2m['/spaced_named']    = root.spaced_named
    u2m["/near/test"]       = root.near.test
    u2m['/sub/bar']         = root.sub.bar
    u2m['/sub/foo']         = root.sub.foo
    u2m['/sub/far/is_here'] = root.sub.far.is_here

    for path, method in u2m.items():
        request = TestRequest([], path)
        action = site.routeRequest(request)
        assert getattr(action, "func", None) == method, "Expecting %s but got %s for URL %s" %(method, action, path)

def test_prevents_underscores():
    request = TestRequest([], "/sub/__dict__/")

    action = make_new_graph().routeRequest(request)

    assert isinstance(action, NoResource)


def test_handles_defaults_correctly():
    u2m = {}
    site = make_new_graph()
    root = site.resource
    u2m['/doesn/t/exist'] = root.__default__
    u2m['/sub/doesn/t/exist'] = root.sub.__default__

    for path, method in u2m.items():
        request = DummyRequest([])
        request.path = path
        action = site.routeRequest(request)
        assert isinstance(action, NoResource)




if __name__ == '__main__':#pragma: no cover
    nose.run()
