from twisted.web import resource as tw_resource

import pytest

from txweb import web_views
from .helper import ensureBytes, MockRequest



def test_override_404_resource():

    class My404(tw_resource.Resource):

        isLeaf = True

        def render(self, request):
            return "This is a 404"


    website = web_views.WebSite()
    website.setNoResourceCls(My404)

    request = MockRequest("/not/real")
    response = website.getResourceFor(request)

    assert isinstance(response, My404)