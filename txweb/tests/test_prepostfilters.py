#pragma: no cover
from os.path import dirname, abspath, join

from txweb.core import Site
from txweb.util import expose
from txweb.util import OneTimeResource
from txweb.util.testing import MockRequest
from txweb.tests.helper import helper

from twisted.web.test.test_web import DummyRequest
from twisted.web.resource import ErrorPage
from twisted.web.static import File
from twisted.web.server import NOT_DONE_YET
from twisted.web.static import DirectoryLister



relPath = lambda filename : abspath(join(dirname(__file__), "test_data" , filename))


#todo find a viable mock library
class Root(object):

    def _prefilter(self, request):
        self.preFilterWasCalled = True

    @expose
    def anAction(self, request):
        return "anActionWasCalled"

    def _postfilter(self, request, response):
        self.postFilterWasCalled = True

def test_filtersAreCalled():
    root = Root()
    site = Site(root)
    request = MockRequest([],"/anAction")
    action = site.routeRequest(request)
    helper.assertIsInstance(action, OneTimeResource)
    helper.assertEqual(action.func, root.anAction)

    response = action.render(request)
    helper.assertEqual(response, "anActionWasCalled".encode())

    helper.assertTrue(root.preFilterWasCalled)
    helper.assertTrue(root.postFilterWasCalled)

if __name__ == '__main__':
    import pytest
    pytest.main()
