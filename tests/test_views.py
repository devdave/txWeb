from txweb import NOT_DONE_YET
from txweb import web_views


def hanging_view(_):
    yield NOT_DONE_YET
    yield "Hello World"


def string_view(_, word: str):
    return word


def test__process_route__matches():

    def mock(_, number):
        return _, number

    # todo break in two tests

    test_no_trail_url = "/foo/bar/123"
    test_no_trail_route_str = "/foo/bar/<number:int>"
    actual_no_trail_route = web_views.process_route(test_no_trail_route_str, mock)
    actual_no_trail_matches = actual_no_trail_route.matches(test_no_trail_url)

    assert actual_no_trail_matches is True


def test__process_route__matches_trailing_slash():

    def mock(_, number):
        return _, number

    test_trail_url = "/foo/bar/123/"
    test_trail_route_str = "/foo/bar/<number:int>/"
    actual_trail_route = web_views.process_route(test_trail_route_str, mock)
    actual_trail_matches = actual_trail_route.matches(test_trail_url)

    assert actual_trail_route.raw_regex == f"^/foo/bar/(?P<number>.*)/$"
    assert actual_trail_matches is True


def test__process_route__calls_int_type_correctly():

    def stub(request, argument1):
        return argument1

    class Request123:
        path = "/foo/bar/123/"


    test_number_url = "/foo/bar/123/"
    test_route_str = "/foo/bar/<number:int>/"
    actual_route = web_views.process_route(test_route_str, stub)

    actual_result = actual_route.run(Request123())
    assert actual_result == 123


def test__process_route__calls_str_type_correctly():

    def stub(request, argument1):
        return argument1

    class Request123:
        path = "/foo/bar/word/"

    test_route_str = "/foo/bar/<a_word:str>/"
    actual_route = web_views.process_route(test_route_str, stub)

    actual_result = actual_route.run(Request123())
    assert actual_result == "word"


def test__add_route():

    class RequestStubString:
        path = "/foo/bar/thing_string/"

    class RequestStubNumber:
        path = "/foo/bar/4567/"

    @web_views.add("/foo/blah/<thing_str:str>/")
    def stub(request, thing_str):
        return thing_str

    @web_views.add("/foo/bar/<thing_number:int>")
    def stub2(request, thing_int):
        return thing_int

    action = web_views.site.getResourceFor(RequestStubNumber())

    assert action.func == stub2


def test__Site_getResourceFor__returns_NoResource_if_no_match():

    class RequestBad:
        path = "/no/match/url"

    @web_views.add("/foo/bar/<number:int>")
    def stub(request, number):
        return number

    action = web_views.site.routeRequest(RequestBad())

    assert isinstance(action, web_views.NoResource)


def test_Site_getResourceFor__returns_ActionResource_if_match():

    class MatchingPath:
        path = "/foo/bar/a_number_follows/123/"

    @web_views.add("/foo/bar/a_number_follows/<number:int>/")
    def stub(request, number):
        return number


    action = web_views.site.routeRequest(MatchingPath())
    assert isinstance(action, web_views.resource.Resource)
    assert action.render(MatchingPath()) == 123