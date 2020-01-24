import pytest
import inspect


def decorator(prefix=None, debug=False):
    if isinstance(prefix, str) is not True:
        raise ValueError("class decorator Requires str prefix")

    def processor(obj):
        assert inspect.isclass(obj)
        rules = [
            getattr(x, "__route__") for k, x in getattr(obj, "__dict__").items() if
            inspect.isfunction(x) and hasattr(x, "__exposed__")
        ]
        if rules and debug is True:
            setattr(obj, "__subrules__", rules)

        return obj

    return processor


def expose(route, **kwargs):
    def processor(obj):
        setattr(obj, "__exposed__", True)
        setattr(obj, "__route__", (obj.__name__, route, kwargs))
        return obj

    return processor

def test_class_def_decorator():


    @decorator("/prefix", debug=True)
    class Foo(object):

        @expose("/bar")
        def bar(self):
            pass

        @expose("/blah")
        def baz(self):
            pass


    assert hasattr(Foo, "__subrules__")
    assert getattr(Foo.bar, "__exposed__") is True
    assert len(Foo.__subrules__) == 2

    func_obj_name, route, kwargs = Foo.__subrules__[0]
    assert func_obj_name == "bar"

def test_decorator_knows_route_str_is_required():

    with pytest.raises(ValueError):
        @decorator()
        class Foo():
            pass

    @decorator("/blah")
    class Foo():
        pass


def test_sanity_check_dict_update():

    actual = dict(a=1, b=2)
    actual.update(dict(b=3, c=2))
    expected = dict(a=1, b=3, c=2)

    assert actual == expected

