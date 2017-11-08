

#pragma: no cover
import pytest

from inspect import signature

from txweb.sugar.smartcontroller import FindDirectives
from txweb.sugar.smartcontroller import SmartController
from txweb.sugar.smartcontroller import SafeStr

from txweb.util import expose
from txweb.tests.helper import helper

from twisted.web.test.test_web import DummyRequest

class BlankController():

    def action_basic(self, request):
        pass

    def action_argument(self, request, a_first:SafeStr=None):
        pass

    def action_list(self, request, al_vars=None):
        pass

    def action_composite(self, request, a_first=None, al_vars=None):
        pass

class ExampleController(metaclass=SmartController):

    @expose
    def simple_method(self, request):
        return locals()

    def action_testmethod(self, request):
        return locals()

    def action_annotated(self, request, a_first:SafeStr = None):
        return {"a_first":a_first}
        
    def action_args(self, request, a_first = None, a_second = None, a_third = None):
        return {"a_first":a_first, "a_second":a_second,"a_third":a_third}

    def action_collected(self, request, c_thing = None):
        return {"c_thing":c_thing}

    def action_collected_annotated(self, request, c_thing:SafeStr = None):
        return {"c_thing":c_thing}

    def action_list_of_arguments(self, request, al_state:int=None):
        return {"al_state":al_state}
        
    def action_requestattrs(self, request, r_args = None, r_foo = None):
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


def test_obeys_annotations():
    request = DummyRequest([])
    econ = ExampleController()
    request.addArg(b"first", 123)

    actual = econ.annotated(request)
    assert actual["a_first"] == "123"

def test_obeys_annotation_handles_bytes():
    request = DummyRequest([])
    econ = ExampleController()
    request.addArg(b"first", b"this is bytes")

    actual = econ.annotated(request)
    assert actual["a_first"] == "this is bytes"

def test_annotations_dont_cause_type_error_when_no_input_provided():
        request = DummyRequest([])
        controller = ExampleController()
        actual = controller.annotated(request)
        assert actual == dict(a_first=None)
    
def test_verify_prefixed_args():
    controller = ExampleController()
    request = DummyRequest([])
    request.addArg(b"thing_size", b"giant")
    request.addArg(b"thing_color", b"purple")
    request.addArg(b"thing_vocation", b"people eater")

    actual = controller.collected(request)
    assert actual["c_thing"] == {"size":b"giant", "color":b"purple", "vocation":b"people eater"}

def test_verify_prefixed_args_obey_annotation():
    controller = ExampleController()
    request = DummyRequest([])
    request.addArg(b"thing_size", b"giant")
    request.addArg(b"thing_color", b"purple")
    request.addArg(b"thing_vocation", b"people eater")

    actual = controller.collected_annotated(request)
    assert actual["c_thing"] == {"size":"giant", "color":"purple", "vocation":"people eater"}


def test_varify_argumentlist():
    controller = ExampleController()
    request = DummyRequest([])
    request.args[b"state"] = [b"0",b"1",b"2",b"3"]


    actual = controller.list_of_arguments(request)
    assert actual["al_state"] == [0,1,2,3]

    
def test_verify_directives_ensure_basic_is_empty():
    
    directives = FindDirectives(BlankController.action_basic)
    assert len(directives.afirst) == 0

def test_directives_detected_argument_kwparam():
    directives = FindDirectives(BlankController.action_argument)
    assert len(directives.afirst) == 1

    assert directives.afirst[0].str_name == "first"

def test_directives_detected_argument_kwlist():
    directives = FindDirectives(BlankController.action_list)
    assert len(directives.alist) == 1
    assert directives.alist[0].str_name == "vars"
    
    

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
        assert hasattr(eCon, name) == True, dir(eCon)


def test_argshandlingLogic(testClass):

    request = DummyRequest([])
    eCon = testClass()
    expected = {
        "a_first" : b"Hello",
        "a_second" : b"World",
        "a_third" : None
    }

    request.addArg(b"first", expected["a_first"])
    request.addArg(b"second", expected["a_second"])

    actual = eCon.args(request)

    assert actual == expected


def test_requestAttrHandlingLogic(testClass):

    request = DummyRequest([])
    actual = testClass().requestattrs(request)
    assert actual['r_foo'] == None


def test_default_Arguments_Works_As_Expected(testClass):

    emptyRequest = DummyRequest([])
    populatedRequest = DummyRequest([50])
    populatedRequest.addArg(b"name", b"John Doe")

    controller = testClass()
    actuals1 = controller.defaultArguments(emptyRequest)
    actuals2 = controller.defaultArguments(populatedRequest)
    expected1 = {

        "a_name": "Unknown",
        "request": emptyRequest,
        "self": controller
    }
    expected2 = {
        "a_name": b"John Doe",
        "request": populatedRequest,
        "self": controller
    }
    assert actuals1 == expected1
    assert actuals2 == expected2
    # helper.assertDictEqual(actuals1, expected1)



def test_everything_method():
    postPath = ["first", "second"]
    request = DummyRequest(postPath)
    request.addArg(b"foo", b"hello")
    request.addArg(b"bar", b"world")

    eCon = ExtendedController()

    expectedReturn = {
        'self': eCon,
        "request": request,
        "a_foo": b"hello",
        "a_bar": b"world",
        'r_args': {b'bar': [b'world'], b'foo': [b'hello']},
        'r_postpath': ['first', 'second']
        }

    actuals = eCon.everything(request)
    assert expectedReturn == actuals
    assert 1 == 1
    



if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
