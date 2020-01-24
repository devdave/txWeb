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



def test_provides_pre_and_post_filter_support(dummy_request):
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

    debug = 1

