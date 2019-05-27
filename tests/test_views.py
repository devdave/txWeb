
from txweb import NOT_DONE_YET
from txweb import web_views

def hanging_view(request):
    yield NOT_DONE_YET
    yield "Hello World"

def string_view(request, word:str):
    return "A String"



def test__process_route__matches():

    mock = lambda _, number: (_, number)

    #todo break in two tests

    test_no_trail_url = "/foo/bar/123"
    test_no_trail_route_str = "/foo/bar/<number:int>"
    actual_no_trail_route = web_views.process_route(test_no_trail_route_str, mock)
    actual_no_trail_matches = actual_no_trail_route.matches(test_no_trail_url)

    assert actual_no_trail_matches is True



def test__process_route__matches_trailing_slash():

    mock = lambda _, number: (_, number)

    test_trail_url = "/foo/bar/123/"
    test_trail_route_str = "/foo/bar/<number:int>/"
    actual_trail_route = web_views.process_route(test_trail_route_str, mock)
    actual_trail_matches = actual_trail_route.matches(test_trail_url)

    assert actual_trail_route.raw_regex == f"^/foo/bar/(?P<number>.*)/$"
    assert actual_trail_matches is True