

from txweb.sugar.quick import QuickParam
from txweb.sugar.quick import ReqAttr
from txweb.sugar.quick import QArg


class BaseController(metaclass=QuickParam):
    pass


class FixedController(BaseController):

    def action_args(self, request, foo:QArg(str) = None, bar:QArg = None):
        return dict(foo=foo, bar=bar)

    def action_request_var(self, request, args:ReqAttr(None) = None):
        return dict(args=args)



def test_action_is_exposed():

    controller = FixedController()

    assert hasattr(controller, "args")
    assert hasattr(controller.args, "exposed")



if __name__ == "__main__":
    import pytest
    pytest.main([__file__])


