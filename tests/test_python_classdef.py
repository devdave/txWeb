import inspect

def test_class_def_decorator():

    matches = []

    def decorator(debug=False):

        def processor(obj):
            assert inspect.isclass(obj)
            rules = [
                getattr(x, "__route__") for k,x in getattr(obj, "__dict__").items() if inspect.isfunction(x) and hasattr(x, "__exposed__")
            ]
            if rules and debug is True:
                setattr(obj, "__subrules__", rules)

            return obj
        return processor

    def expose(route, **kwargs):

        def processor(obj):
            setattr(obj, "__exposed__", True)
            setattr(obj, "__route__", (route, kwargs))
            return obj

        return processor


    @decorator(debug=True)
    class Foo(object):

        @expose("/bar")
        def bar(self):
            pass

        @expose("/blah")
        def baz(self):
            pass


    assert hasattr(Foo, "__subrules__")
    assert getattr(Foo.bar, "__exposed__") is True
