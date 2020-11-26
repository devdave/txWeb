import functools
import pytest

def test_boundmethod_decorator():


    def decorator1(func):

        @functools.wraps(func)
        def processor(*args, **kwargs):
            # for position, arg in enumerate(args):
            #     print(f"{position}, {arg!r}")


            return func(*args, **kwargs)
        return processor

    def decorator2(func):
        def processor(arg1, arg2):
            return func(arg1, arg2)

        return processor

    def decorator3(func):
        def processor(parent, arg1, arg2):
            return func(parent, arg1, arg2)

        return processor


    class ToyClass:

        @decorator1
        def method1(self, arg1, kw1=None):
            pass

        @decorator2
        def method2(self, arg1, arg2):
            pass

        @decorator3
        def method3(self, arg1, arg2):
            pass

        @decorator3
        def method4(*args, **kwargs):
            pass
            # for position, arg in enumerate(args):
            #     print(f"{position}: {arg!r}")


    instance = ToyClass()
    #
    # print()
    # print("Starting decorator types test")

    instance.method1("Hello World", kw1="Foo")

    with pytest.raises(TypeError):
        instance.method2("Hello", "World")

    instance.method3("Foo", "Bar")

    instance.method4("Hello", "World!")