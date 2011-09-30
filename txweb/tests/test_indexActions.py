#pragma: no cover
from os.path import dirname, abspath, join
import nose

from txweb.core import Site
from txweb.util import expose
from txweb.util.testing import TestRequest

from twisted.web.test.test_web import DummyRequest
from twisted.web.resource import ErrorPage
from twisted.web.static import File
from twisted.web.server import NOT_DONE_YET
from twisted.web.static import DirectoryLister

relPath = lambda filename : abspath(join(dirname(__file__), "test_data" , filename))

class Sub(object):
    index = File(relPath("a.txt"))

class Root(object):
    sub = Sub()
    
    
    
siteWithSubControllerWithFileIndex = Site(Root())

def test_path2controllerResolvesToIndex():
    """
        Regression found in WebMud 1.4 project where sub controller's that have
        index == File() are not resolving correctly when given a path line "/parent/"
        which should resolve to Root.parent.index
        
    """
    request = TestRequest([],"/sub/")
        
    action = siteWithSubControllerWithFileIndex.routeRequest(request)
    response = action.render(request)
    assert response == NOT_DONE_YET
    
    with open(relPath("a.txt"), "rb") as testFile:
        expected = testFile.read()
        assert len(request.written) ==  1, "Expected written log to be equal to one"
        actualSize = len(request.written[0])
        expectedSize = len(expected)
        actual = request.written[0]
        assert expectedSize == actualSize, "Expected size doesn't match actual"
        assert expected == actual, "Expecting actual written body to equal expected body"
    
    
if __name__ == '__main__':#pragma: no cover
    nose.run()