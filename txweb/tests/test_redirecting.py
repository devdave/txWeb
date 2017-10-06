"""
    NOTE: Attempt to re-org tests by problem and less by originating code

    Tests for handling odd/undesirable routing issues
"""


#pragma: no cover
from os.path import dirname, abspath, join


from txweb.core import Site
from txweb.util import expose
from txweb.util.testing import TestRequest


from twisted.web.resource import ErrorPage
from twisted.web.static import File
from twisted.web.server import NOT_DONE_YET
from twisted.web.static import DirectoryLister
from twisted.web.util import Redirect

class SubClass(object):

    @expose
    def index(self, request):
        return "Hello World!"

class ExampleRoot(object):
    subclass = SubClass()

site = Site(ExampleRoot)

def test_redirectIfPathPointsToAnAttributeObject():
    request = TestRequest([], "/subclass")

    result = site.routeRequest(request)
    assert isinstance(result, Redirect )
    assert result.url == "/subclass/"
    result.render(request)
    request.redirectToURL == "/subclass/"
    dbg = 1


