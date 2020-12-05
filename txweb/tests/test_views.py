
from twisted.web import resource as tw_resource

import pytest

from txweb import web_site
from .helper import ensureBytes, MockRequest

# def getChildForRequest(resource, request):
#     """
#     Traverse resource tree to find who will handle the request.
#     """
#     while request.postpath and not resource.isLeaf:
#         pathElement = request.postpath.pop(0)
#         request.prepath.append(pathElement)
#         resource = resource.getChildWithDefault(pathElement, request)
#     return resource


# def test__website_add__works():
#
#     test_website = web_views.WebSite()
#     expected_number_value = 890
#     request = MockRequest([], f"/foo/bar/{expected_number_value}")
#
#     @test_website.add("/foo/bar/<int:a_number>")
#     def stub(request, a_number):
#         assert expected_number_value == a_number
#         return a_number
#
#     rsrc = test_website.getResourceFor(request)
#
#     assert rsrc.func == stub


# def test_website_add__handles_native_resources():
#
#     test_website = web_views.WebSite()
#     expected_number_value = 890
#     request = MockRequest([], f"/foo/bar/{expected_number_value}")
#
#     @test_website.add("/foo/bar/<int:number>")
#     class TestResource(tw_resource.Resource):
#         isLeaf = True
#
#         def render(self, request):
#             assert "number" in request.route_args
#             assert request.route_args["number"] == expected_number_value
#             return b"Rendered TestResource"
#
#     rsrc = test_website.getResourceFor(request)
#     assert isinstance(rsrc, TestResource)
#     assert rsrc.render(request) == b"Rendered TestResource"


# def test_website__adds_resource_class():
#
#     test_website = web_views.WebSite()
#
#     test_website.add("/foo")(tw_resource.NoResource)
#
#
#     request = MockRequest([], "/foo")
#     rsrc = test_website.getResourceFor(request)
#
#     assert isinstance(rsrc, tw_resource.NoResource)


# def test_website__able_to_access_routing_rules():
#
#     site = web_views.WebSite()
#
#     @site.add("/foo")
#     def foo_view(request):
#         pass
#
#     @site.add("/bar")
#     def bar_view(request):
#         pass
#
#     rules = list(site.resource.iter_rules())
#
#     assert len(rules) == 2
#     assert rules[0].rule == "/foo"





