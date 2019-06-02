#txweb imports

#twisted imports

from twisted.web import resource
from twisted.web import server
from twisted.web.resource import NoResource
from twisted.web.server import NOT_DONE_YET
from twisted.internet import defer

#stdlib
import re
from collections import OrderedDict
import inspect

class ViewResource(resource.Resource):

    isLeaf = True # Disable dynamic resource mechanism in twisted.web

    def __init__(self, routing_str, func, double_slash_warning=True, coerce_str_to_bytes=True):
        self.routing_str = routing_str
        self.func = func
        self.double_slash_warning = double_slash_warning
        self.coerce_str_to_bytes = coerce_str_to_bytes
        self.regex = None
        self.route_rules = None

        self.process_route(self.routing_str)

        resource.Resource.__init__(self)

    def process_route(self, routing_str):
        segments = routing_str.split("/")
        raw_regex = []
        match_rules = {}

        trailing_slash = routing_str.endswith("/")

        if "//" in routing_str:
            if self.double_slash_warning is True:
                print("Warning: there is a double slash (//) in route")

        for segment in segments:
            if segment.startswith("<"):
                name, name_type = segment[1:-1].split(":")
                match_rules[name] = name_type
                re_segment = f"(?P<{name}>.*)"
                re_segment = f"(?P<{name}>.[^/]*)"
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

        self.regex = re.compile(raw_regex)
        self.route_rules = match_rules

    def run(self, request):
        str_request_path = request.path.decode()

        matches = self.regex.match(str_request_path)

        vargs = [request]
        kwargs = OrderedDict()

        def eval_type(type_str, value):
            transform = eval(type_str, self.func.__globals__)
            return transform(value)

        for rule_name in self.route_rules:
            kwargs[rule_name] = eval_type(self.route_rules[rule_name], matches[rule_name])

        vargs += kwargs.values()


        result = self.func(*vargs)
        if isinstance(result, defer.Deferred):
            return NOT_DONE_YET
        else:

            if result is NOT_DONE_YET:
                pass
            # TODO this could be problematic if the "wrong" data is returned
            elif self.coerce_str_to_bytes is True:
                if isinstance(result, str):
                    result = result.encode()
                elif isinstance(result, bytes) is False:
                    result = str(result).encode()

            return result

    def render(self, request):
        return self.run(request)

    def getChild(self, child_name, request):
        return self






class WebSite(server.Site):

    def __init__(self):
        self.routes = {}
        self.double_slash_warning = True

        self.no_resource_cls = NoResource

        server.Site.__init__(self, self.no_resource_cls())


    def add(self, route_str):

        def decorator(func):
            action = ViewResource(route_str, func, self.double_slash_warning)
            self.routes[action.regex] = action

            return func

        return decorator

    def getResourceFor(self, request):

        str_request_path = request.path.decode()

        for path_regex, web_resource in self.routes.items():
            if path_regex.match(str_request_path) is not None:
                return web_resource
        else:
            return self.no_resource_cls()




website = WebSite()
add = website.add
