from functools import wraps
import inspect
import re
from collections import OrderedDict

def process_route(route_str, func, double_slash_warn=True):
    segments = route_str.split("/")
    raw_regex = []
    scope = None
    match_rules = {}

    trailing_slash = route_str.endswith("/")

    if "//" in route_str:
        if double_slash_warn is True:
            print("Warning: there is a double slash (//) in route")

    for segment in segments:
        if segment.startswith("<"):
            name, type = segment[1:-1].split(":")
            match_rules[name] = type
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



class WebRoute(object):


    def __init__(self, raw_regex, func, rules={}):
        self.raw_regex = raw_regex
        self.func = func
        self.regex = re.compile(self.raw_regex)
        self.signature = inspect.signature(func)
        self.is_generator = inspect.isgenerator(func)


    def matches(self, url):
        return self.regex.match(url) is not None

    def run(self, request):
        matches = self.regex.match(url)

        vargs = [request]
        #currently unused as is
        kwargs = matches.groupdict()
        vargs += kwargs.values()

        return self.func(*vargs)





if __name__ == "__main__":
    import pytest
    pytest.main()