#pragma: no cover
import unittest
import nose
from nose import tools as ntools

from txweb.sugar.smartcontroller import SmartController
from txweb.util import expose

from twisted.web.test.test_web import DummyRequest

class ExampleController(object):
    
    __metaclass__ = SmartController
    
    @expose
    def simple_method(self, request):
        return locals()
        
    def action_testmethod(self, request):#pragma: no cover
        return locals()
        
    def action_args(self, request, a_first = None, a_second = None, a_third = None):
        return locals()
        
    
    def action_requestattrs(self, request, r_store = None, r_foo = None):
        return locals()
    
    def action_postpathargs(self, request, u_first = None, u_second = None, u_third = None):
        return locals()
        
def test_simple_method_isunchanged():
    eCon = ExampleController()
    request = DummyRequest([])
    assert hasattr(eCon, "simple_method")
    assert hasattr(eCon.simple_method, "exposed")
    response = eCon.simple_method(request)
    assert response['request'] == request
    assert response['self'] == eCon
    
def test_actions_were_renamed():
    eCon = ExampleController()
    for name in ['testmethod', 'args', 'requestattrs']:
        assert hasattr(eCon, name) == True, "Expecting action_%s to be renamed to %s" %(name, name)
        

def test_argshandlingLogic():
    
    request = DummyRequest([])
    firstArgument = "Hello"
    secondArgument = "World"
    thirdArgument = None
    
    request.addArg("first", firstArgument)
    request.addArg("second", secondArgument)
    
    eCon = ExampleController()    
    expected = {"self": eCon, "a_first" : [firstArgument], "a_second" : [secondArgument], "a_third" : None}
    actual = eCon.args(request)
    for key in expected.keys():
        assert actual.get(key, ['unique object']) == expected[key], "Missing expected key %s in %r" % (key, actual)
    
def test_requestAttrHandlingLogic():
    request = DummyRequest([])
    expectedStoreValue = {"data":"store"}
    expectedFooValue = None
    setattr(request, 'store', expectedStoreValue )
    actual = ExampleController().requestattrs(request)
    assert actual['r_store'] == expectedStoreValue
    assert actual['r_foo'] == None
    
def test_postPathArgsHandlingLogic():
    postPath = ["first argument", "second argument"]
    request = DummyRequest(postPath)
    actuals = ExampleController().postpathargs(request)
    assert postPath == [actuals['u_first'], actuals['u_second']]
    assert actuals['u_third'] is None
    
if __name__ == '__main__': #pragma: no cover
    nose.run()
    