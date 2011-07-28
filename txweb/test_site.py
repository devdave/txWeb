
import nose
from core import Site
from util import expose

from twisted.web.test.test_web import DummyRequest

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
    

root = Root()
site = Site(root)

def test_site_routeRequestCorrectly():
    u2m = {}
    u2m["/"] = root.index
    u2m['/spaced_named']    = root.spaced_named
    u2m["/near/test"]       = root.near.test
    u2m['/sub/bar']         = root.sub.bar
    u2m['/sub/foo']         = root.sub.foo
    u2m['/sub/far/is_here'] = root.sub.far.is_here
    
    for path, method in u2m.items():
        request = DummyRequest([])
        request.path = path
        action = site.routeRequest(request)
        assert action.func == method, "Expecting %s but got %s for URL %s" %(method, action, path)    

def test_prevents_underscores():
    request = DummyRequest([])
    request.path = "/sub/__dict__/"
    action = site.routeRequest(request)
    response = action.render(request)
    assert response == "500 URI segments cannot start with an underscore"
    
def test_handles_defaults_correctly():
    u2m = {}
    u2m['/doesn/t/exist'] = root.__default__
    u2m['/sub/doesn/t/exist'] = root.sub.__default__
    
    for path, method in u2m.items():
        request = DummyRequest([])
        request.path = path
        action = site.routeRequest(request)
        assert action.func == method, "Expecting %s but got %s for URL %s" %(method, action, path)
        

if __name__ == '__main__':#pragma: no cover
    nose.run()
