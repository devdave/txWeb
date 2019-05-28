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


def test__process_route__calls():
    pass
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
