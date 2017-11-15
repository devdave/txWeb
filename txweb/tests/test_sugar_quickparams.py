

from txweb.sugar.quick import QuickParams
from txweb.sugar.quick import RequestArg


class BaseController(object):
    __metaclass__ = QuickParams


class FixedController(BaseController):

    def action_args(self, request, foo:QArg(str) = None, bar:QArg = None):
        return dict(foo=foo, bar=bar)

    def action_request_var(self, request, args:QRequest = None):
        return dict(args=args)



def test_action_is_exposed():

    controller = FixedController()
    assert hasattr(controller, "exposed")
