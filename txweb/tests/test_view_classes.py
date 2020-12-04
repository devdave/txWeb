import pytest
from unittest.mock import sentinel

from txweb.application import Application
from txweb.lib.view_class_assembler import view_assembler, expose, set_prefilter, set_postfilter

from .helper import RequestRetval


def test_correctly_adds_classes_to_routing_map():

    app = Application(__name__)

    @app.add_class("/foo")
    class Foo(object):

        @app.expose("/hello")
        def hello(self, request):
            return b"World"

    assert len(app.router._route_map._rules) == 1
    assert app.router._route_map._rules[0].rule == "/foo/hello"



def test_provides_pre_filter_support(dummy_request:RequestRetval):
    """

    :return:
    """
    branch_result = sentinel.branch_result
    request = dummy_request.request

    class PreFoo(object):

        @expose("/branch")
        def do_branch(self, request):
            raise ValueError("Prefilter not called")

        @set_prefilter
        def _prefilter(self, request, method_name):
            raise RuntimeError("Prefilter called")

    pre_thing = view_assembler("/foo", PreFoo, {})

    #  https://stackoverflow.com/a/39292086/9908
    branch_key = next(iter(pre_thing.endpoints))
    branch_key_resource = pre_thing.endpoints[branch_key]

    assert hasattr(branch_key_resource, "prefilter") is True

    with pytest.raises(RuntimeError) as excinfo:
        branch_key_resource.render(request)

        assert "Prefilter called" in str(excinfo.value)

def test_provides_post_filter_support(dummy_request:RequestRetval):
    """

    :return:
    """
    branch_result = sentinel.branch_result
    request = dummy_request.request

    class PreFoo(object):

        @expose("/branch")
        def do_branch(self, request):
            return "do_branch's output"

        @set_postfilter
        def _postfilter(self, request, request_method, original_body):
            assert original_body == "do_branch's output"
            return "post filter replaced output"

    pre_thing = view_assembler("/foo", PreFoo, {})

    #  https://stackoverflow.com/a/39292086/9908
    branch_key = next(iter(pre_thing.endpoints))
    branch_key_resource = pre_thing.endpoints[branch_key]

    actual = branch_key_resource.render(request)

    # View* resources convert their output to Byte's
    assert actual == b'post filter replaced output'



def test_universal_url_arguments(dummy_request:RequestRetval):

    app = Application(__name__)

    @app.add("/article")
    @app.add("/article/<int:article_id>")
    class Article:

        @expose("/read")
        def do_read(self, request, article_id=None):
            return f"READ:{article_id}"

    dummy_request.site = app.site
    dummy_request.request.requestReceived(b"GET", b"/article/345/read", b"HTTP/1.1")
    actual = dummy_request.read()

    assert actual.endswith(b"READ:345")

def test_stacked_adds(dummy_request:RequestRetval):

    app = Application(__name__)

    @app.add("/article", defaults={"article_id":None})
    @app.add("/article/<int:article_id>")
    class Article:

        @app.expose("/")
        def do_list(self, article_id=None):
            return "A,B,C"

    dummy_request.site = app.site
    dummy_request.request.requestReceived(b"GET", b"/article/", b"HTTP/1.1")
    actual = dummy_request.read()

    assert actual.strip().endswith(b"A,B,C")


def test_find_pre_and_post_filters():

    app = Application(__name__)

    class Test(object):

        @app.set_view_prefilter
        def blank_prefilter(self, request, method_name):
            return None

        @app.set_view_postfilter
        def blank_postfilter(self, request, method_name, response):
            return response

    from txweb.lib.view_class_assembler import find_member, POSTFILTER_ID, PREFILTER_ID

    test = Test()

    assert hasattr(test.blank_postfilter, POSTFILTER_ID) is True
    assert hasattr(test.blank_prefilter, PREFILTER_ID) is True

    actual = find_member(test, POSTFILTER_ID)
    assert actual == test.blank_postfilter

    actual = find_member(test, PREFILTER_ID)
    assert actual == test.blank_prefilter

    bad = find_member(test, "NOT A REAL THING")
    assert bad is False




def test_setting_prefilter(dummy_request:RequestRetval):

    from unittest.mock import sentinel, MagicMock

    app = Application(__name__)


    class WasCalled(Exception):
        pass


    class TestPrefilter(object):

        @app.expose("/foo")
        def stub(self, request):
            return ""

        @app.set_view_prefilter
        def my_prefilter(self, request, method_name):
            raise WasCalled()

    decorated = view_assembler("/test", TestPrefilter, {})
    resource_name, resource = next(iter(decorated.endpoints.items()))
    with pytest.raises(WasCalled):
        result = resource.render(dummy_request.request)



def test_setting_postfilter(dummy_request:RequestRetval):

    from unittest.mock import sentinel

    app = Application(__name__)

    class WasCalled(Exception):
        pass


    class TestPostfilter(object):

        @app.expose("/foo")
        def stub(self, request):
            return ""

        @app.set_view_postfilter
        def my_postfilter(self, request, method_name, response):
            raise WasCalled()

    decorated = view_assembler("/test", TestPostfilter, {})
    resource_name, resource = next(iter(decorated.endpoints.items()))
    with pytest.raises(WasCalled):
        result = resource.render(dummy_request.request)


def test_prefilter_method_name_is_correct(dummy_request:RequestRetval):

    app = Application(__name__)

    class TestPostfilter(object):

        @app.expose("/foo")
        def stub(self, request):
            return ""

        @app.set_view_postfilter
        def my_postfilter(self, request, method_name, response):
            assert method_name == self.stub.__qualname__
            assert method_name.endswith("stub")
            return response

    decorated = view_assembler("/test", TestPostfilter, {})
    resource_name, resource = next(iter(decorated.endpoints.items()))
    result = resource.render(dummy_request.request)


global_test_app = Application(__name__)

class GlobalTestView(object):

    @global_test_app.expose("/foo")
    def exposed(self, request):
        return ""

    @global_test_app.set_view_prefilter
    def my_prefilter(self, request, method_name):
        cls, method = method_name.split(".",1)
        assert cls == "GlobalTestView"
        assert method == "exposed"


def test_verify_method_name_is_correct(dummy_request:RequestRetval):

    decorated = view_assembler("/test", GlobalTestView, {})
    name, resource = next(iter(decorated.endpoints.items()))
    result = resource.render(dummy_request.request)
