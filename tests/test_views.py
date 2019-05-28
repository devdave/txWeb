from txweb import NOT_DONE_YET
from txweb import web_views


def test__website_add__works():

    class StubRequest:
        path = "/foo/bar/890"

    @web_views.add("/foo/bar/<number:int>")
    def stub(request, a_number):
        return a_number

    resource = web_views.website.getResourceFor(StubRequest())
    assert isinstance(resource, web_views.resource.Resource)
    assert isinstance(resource, web_views.ViewResource)
    assert resource.func == stub
    assert resource.render(StubRequest()) == 890


