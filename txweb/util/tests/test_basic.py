from twisted.web.server import NOT_DONE_YET
from twisted.internet import defer

from txweb.util.basic import ActionResource
from txweb.util.basic import OneTimeResource


def test_action_resource_handles_not_done_yet():

    def stub(request):
        return NOT_DONE_YET
    resource = ActionResource(stub)
    assert resource.render({}) == NOT_DONE_YET

def test_action_resource_handles_normal_output():

    FOO = "BAR"
    def stub(request):
        return FOO
    resource = ActionResource(stub)
    assert resource.render({}) == FOO

def test_action_handles_inline_callbacks():

    FOO = "BAR"

    @defer.inlineCallbacks
    def stub(request):
        yield "foo"

    resource = ActionResource(stub)
    assert resource.render({}) == NOT_DONE_YET


#def test_onetime_handles_prefilter():
#    FOO = "BAR"
#
#    def stub(request):
#        return "foo"
#
#    resource = ActionResource(stub)
#    assert resource.render({}) == NOT_DONE_YET
