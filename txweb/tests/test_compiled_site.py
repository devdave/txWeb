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




if __name__ == '__main__':#pragma: no cover
    nose.run()
