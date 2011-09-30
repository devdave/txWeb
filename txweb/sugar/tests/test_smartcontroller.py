

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
        
    def action_testmethod(self):#pragma: no cover
        return locals()
        
    def action_args(self, a_first = None, a_second = None, a_third = None):
        return locals()
        
    
    def action_requestattrs(self, r_store = None, r_foo = None):
        return locals()
    
    def action_postpathargs(self, u_first = None, u_second = None, u_third = None):
        return locals()
        
    def action_defaultArguments(self, u_number = 10, a_name = "Unknown"):
        return locals()
       
class ExtendedController(ExampleController):
    
    def action_everything(self, u_first = None, u_second = None, a_foo = None, a_bar = None, r_args = None, r_postpath = None):
        return locals()
        
        
def test_simple_method_isunchanged(testController = None):
    testClass = testController or ExampleController
    eCon = testClass()
    request = DummyRequest([])
    assert hasattr(eCon, "simple_method")
    assert hasattr(eCon.simple_method, "exposed")
    response = eCon.simple_method(request)
    
    assert response['self'] == eCon
    
def test_actions_were_renamed(testController = None):
    testClass = testController or ExampleController
    eCon = testClass()
    for name in ['testmethod', 'args', 'requestattrs']:
        assert hasattr(eCon, name) == True, "Expecting action_%s to be renamed to %s" %(name, name)
        

def test_argshandlingLogic(testController = None):
    testClass = testController or ExampleController
    
    request = DummyRequest([])
    firstArgument = "Hello"
    secondArgument = "World"
    thirdArgument = None
    
    request.addArg("first", firstArgument)
    request.addArg("second", secondArgument)
    
    eCon = testClass()    
    expected = {"self": eCon, "a_first" : firstArgument, "a_second" : secondArgument, "a_third" : None}
    actual = eCon.args(request)
    for key in expected.keys():
        assert actual.get(key, ['unique object']) == expected[key], "Missing expected key %s in %r" % (key, actual)
    
def test_requestAttrHandlingLogic(testController = None):
    testClass = testController or ExampleController
    request = DummyRequest([])
    expectedStoreValue = {"data":"store"}
    expectedFooValue = None
    setattr(request, 'store', expectedStoreValue )
    
    actual = testClass().requestattrs(request)
    assert actual['r_store'] == expectedStoreValue
    assert actual['r_foo'] == None
    
def test_postPathArgsHandlingLogic(testController = None):
    testClass = testController or ExampleController
    
    postPath = ["first argument", "second argument"]
    request = DummyRequest(postPath)
    actuals = testClass().postpathargs(request)
    assert postPath == [actuals['u_first'], actuals['u_second']]
    assert actuals['u_third'] is None

def test_inheritedController():
    for test in [test_postPathArgsHandlingLogic, test_requestAttrHandlingLogic, test_argshandlingLogic,test_actions_were_renamed,test_simple_method_isunchanged ]:
        test(ExtendedController)


def test_defaultArgumentsWorksAsExpected(testController = None):
    testClass = testController or ExampleController
    emptyRequest = DummyRequest([])
    populatedRequest = DummyRequest([50])
    populatedRequest.addArg("name", "John Doe")
    
    controller = testClass()
    actuals1 = controller.defaultArguments(emptyRequest)
    actuals2 = controller.defaultArguments(populatedRequest)
    assert actuals1['u_number'] == 10, "%s is not equal to %s" % (actuals1['u_number'], 10)
    assert actuals1['a_name'] == "Unknown", "%s is not equal to %s" % (actuals1['a_name'], "Unkown")
    assert actuals2['u_number'] == 50, "%s is not equal to %s" % (actuals2['u_number'], 50)
    assert actuals2['a_name'] == "John Doe", "%s is not equal to %s" % (actuals2['a_name'], "John Doe")
    

def test_everything():
    postPath = ["first argument", "second argument"]
    request = DummyRequest(postPath)
    request.addArg("foo", "hello")
    request.addArg("bar", "world")
    eCon = ExtendedController()
    actuals = eCon.everything(request)    
    assert actuals['u_first'] == postPath[0]
    assert actuals['u_second'] == postPath[1]
    assert actuals['a_foo'] == "hello"
    assert actuals['a_bar'] == "world"



if __name__ == '__main__': #pragma: no cover
    nose.run()
    