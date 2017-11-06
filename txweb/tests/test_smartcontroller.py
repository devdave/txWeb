

#pragma: no cover
import pytest


from txweb.sugar.smartcontroller import SmartController
from txweb.util import expose
from txweb.tests.helper import helper

from twisted.web.test.test_web import DummyRequest

class ExampleController(metaclass=SmartController):

    @expose
    def simple_method(self, request):
        return locals()

    def action_testmethod(self, request):
        return locals()

    def action_args(self, request, a_first = None, a_second = None, a_third = None):
        return locals()


    def action_requestattrs(self, request, r_store = None, r_foo = None):
        return locals()

    def action_defaultArguments(self, request, a_name = "Unknown"):
        return locals()

class ExtendedController(ExampleController):

    def action_everything(self, request, a_foo = None, a_bar = None, r_args = None, r_postpath = None):
        return locals()

@pytest.fixture(scope="session", params=[ExtendedController, ExampleController])
def testClass(request):
    print(f"Testing {type(request.param)}")
    yield request.param


def test_simple_method_isunchanged(testClass):
    #
    eCon = testClass()
    request = DummyRequest([])
    assert hasattr(eCon, "simple_method")
    assert hasattr(eCon.simple_method, "exposed")
    response = eCon.simple_method(request)

    assert response['self'] == eCon

def test_actions_were_renamed(testClass):

    eCon = testClass()
    for name in ['testmethod', 'args', 'requestattrs']:
        assert hasattr(eCon, name) == True, "Expecting action_%s to be renamed to %s" %(name, name)


def test_argshandlingLogic(testClass):

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

def test_requestAttrHandlingLogic(testClass):

    request = DummyRequest([])
    expectedStoreValue = {"data":"store"}
    expectedFooValue = None
    setattr(request, 'store', expectedStoreValue )

    actual = testClass().requestattrs(request)
    assert actual['r_store'] == expectedStoreValue
    assert actual['r_foo'] == None


def test_defaultArgumentsWorksAsExpected(testClass):

    emptyRequest = DummyRequest([])
    populatedRequest = DummyRequest([50])
    populatedRequest.addArg("name", "John Doe")

    controller = testClass()
    actuals1 = controller.defaultArguments(emptyRequest)
    actuals2 = controller.defaultArguments(populatedRequest)
    expected1 = {

        "a_name": "Unknown",
        "request": emptyRequest,
        "self": controller
    }
    expected2 = {
        "a_name": "John Doe",
        "request": populatedRequest,
        "self": controller
    }
    assert actuals1 == expected1
    assert actuals2 == expected2
    # helper.assertDictEqual(actuals1, expected1)



def test_everything_method():
    postPath = ["first", "second"]
    request = DummyRequest(postPath)
    request.addArg("foo", "hello")
    request.addArg("bar", "world")

    eCon = ExtendedController()

    expectedReturn = {
        'self': eCon,
        "request": request,
        "a_foo": "hello",
        "a_bar": "world",
        'r_args': {'bar': ['world'], 'foo': ['hello']},
        'r_postpath': ['first', 'second']
        }

    actuals = eCon.everything(request)
    helper.assertEqual(expectedReturn, actuals)
