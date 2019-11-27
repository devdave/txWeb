from twisted.web import resource as tw_resource

import pytest

from txweb import web_views
from .helper import ensureBytes, MockRequest



def test_override_404_resource():

    class My404(tw_resource.Resource):
        def render(self):
            return "There was an error"


    website = web_views.WebSite()

    @website.onError
    def handle_error(site, exc):
        return My404()


    request = MockRequest("/not/real")
    response = website.getResourceFor(request)

    assert isinstance(response, My404)