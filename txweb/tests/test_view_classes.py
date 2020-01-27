import pytest
from unittest.mock import sentinel

from txweb.application import Application
from txweb.lib.view_class_assembler import view_assembler, expose


def test_correctly_adds_classes_to_routing_map():

    app = Application(__name__)

    @app.add_class("/foo")
    class Foo(object):

        @app.expose("/hello")
        def hello(self, request):
            return b"World"

    assert len(app.router._route_map._rules) == 1
    assert app.router._route_map._rules[0].rule == "/foo/hello"



def test_provides_pre_filter_support(dummy_request):
    """

    :return:
    """
    branch_result = sentinel.branch_result
    request = dummy_request.request

    class PreFoo(object):

        @expose("/branch")
        def do_branch(self):
            raise ValueError("Prefilter not called")

        def _prefilter(self, request):
            raise RuntimeError("Prefilter called")

    pre_thing = view_assembler("/foo", PreFoo, {})

    #  https://stackoverflow.com/a/39292086/9908
    branch_key = next(iter(pre_thing.endpoints))
    branch_key_resource = pre_thing.endpoints[branch_key]

    assert hasattr(branch_key_resource, "prefilter") is True

    with pytest.raises(RuntimeError) as excinfo:
        branch_key_resource.render(request)

        assert "Prefilter called" in str(excinfo.value)

def test_provides_post_filter_support(dummy_request):
    """

    :return:
    """
    branch_result = sentinel.branch_result
    request = dummy_request.request

    class PreFoo(object):

        @expose("/branch")
        def do_branch(self, request):
            return "do_branch's output"

        def _postfilter(self, request, original_body):
            assert original_body == "do_branch's output"
            return "post filter replaced output"

    pre_thing = view_assembler("/foo", PreFoo, {})

    #  https://stackoverflow.com/a/39292086/9908
    branch_key = next(iter(pre_thing.endpoints))
    branch_key_resource = pre_thing.endpoints[branch_key]

    actual = branch_key_resource.render(request)

    # View* resources convert their output to Byte's
    assert actual == b'post filter replaced output'



def test_universal_url_arguments(dummy_request):

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

def test_stacked_adds(dummy_request):

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


