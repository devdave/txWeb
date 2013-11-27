
from nose.tools import raises

import json

from twisted.web.server import NOT_DONE_YET

from txweb import expose
from txweb.sugar.filters import json_out
from txweb.util.util_test import TestRequest



class TestException(Exception):
    pass

@json_out
def errornous_method(request):
    raise TestException()

@json_out
def passthru_dict(request):
    return request.args.get('response', {})

class MockWeb(object):


    @expose
    @json_out
    def endpoint(self, request):
        return request.args.get('response', {})



def test_runs_without_error():
    req = TestRequest("")

    x = passthru_dict(req)
    value = json.loads(x)
    assert 'success' in value
    assert value['success'] == True

def test_runs_object_without_error():
    req = TestRequest("")
    root = MockWeb()
    x = root.endpoint(req)
    value = json.loads(x)
    assert 'success' in value
    assert value['success'] == True

@raises(ValueError)
def test_blows_up_on_bad_arguments():
    req = TestRequest("")

    @json_out
    def bad_func():
        pass

    bad_func()


def test_does_not_mangle_success_key():
    req = TestRequest("")
    req.args['response'] = {'success':False}
    x = passthru_dict(req)
    value = json.loads(x)
    assert 'success' in value
    assert value['success'] == False

def test_reports_exceptions():
    req = TestRequest("")
    x = errornous_method(req)

    value = json.loads(x)
    assert value['success'] == False
    assert value['error_type'] == "test_filters.TestException"
    assert value['error'] == ""
    assert req.outgoingHeaders['content-type'] == 'application/json'

def test_handles_not_done_yet_correctly():
    req = TestRequest("")
    req.args['response'] = NOT_DONE_YET
    x = passthru_dict(req)
    assert x == NOT_DONE_YET


def test_assure_content_type():
    req = TestRequest("")
    req.args['response'] = {'success':False, "foo":"bar", "number":1234}
    passthru_dict(req)
    assert req.outgoingHeaders['content-type'] == 'application/json'
