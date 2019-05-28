#twisted imports
from twisted.web import server
from twisted.web.resource import NoResource
from twisted.web import resource

from functools import wraps
import sys
import inspect
import re
from collections import OrderedDict




def process_route(route_str, func, double_slash_warn=True):
    segments = route_str.split("/")
    raw_regex = []

    match_rules = {}

    trailing_slash = route_str.endswith("/")

    if "//" in route_str:
        if double_slash_warn is True:
            print("Warning: there is a double slash (//) in route")

    for segment in segments:
        if segment.startswith("<"):
            name, name_type = segment[1:-1].split(":")
            match_rules[name] = name_type
            re_segment = f"(?P<{name}>.*)"
            raw_regex.append(re_segment)

        elif ">" in segment:
            raise ValueError("Missing < to match >")

        elif segment == "":
            pass
        else:
            raw_regex.append(segment)

    raw_regex.insert(0, "^")
    raw_regex = "/".join(raw_regex)

    if trailing_slash is True:
        raw_regex += "/"

    raw_regex += "$"

    return WebRoute(raw_regex, func, rules=match_rules)


class WebRoute(resource.Resource):

    def __init__(self, raw_regex, func, rules=None):
        self.raw_regex = raw_regex
        self.func = func
        self.regex = re.compile(self.raw_regex)
        self.rules = rules
        self.signature = inspect.signature(func)
        self.is_generator = inspect.isgenerator(func)

    def matches(self, url):
        return self.regex.match(url) is not None

    def run(self, request):
        matches = self.regex.match(request.path)

        vargs = [request]
        kwargs = OrderedDict()


        def eval_type(type_str, value):
            transform = eval(type_str, self.func.__globals__)
            return transform(value)


        for rule_name in self.rules:
            kwargs[rule_name] = eval_type(self.rules[rule_name], matches[rule_name])

        vargs += kwargs.values()

        return self.func(*vargs)

    def render(self, request):
        return self.run(request)


class Site(object):

    def __init__(self):
        self.routes = {}

    def add(self, route_str):

        if isinstance(route_str, str) is False:
            raise ValueError(f"Expecting {route_str} to be <type str>")

        def decorator(func):

            processed_route = process_route(route_str, func)
            self.routes[processed_route.regex] = processed_route
            return func

        return decorator


    def routeRequest(self, request):
        for route_regex, route in self.routes.items():
            if route_regex.match(request.path) is not None:
                return route

        else:
            return NoResource()


site = Site()
add = site.add


if __name__ == "__main__":
    import pytest
    pytest.main()
