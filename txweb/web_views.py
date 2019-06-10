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
import copy

class ViewResource(resource.Resource):

    isLeaf = True # Disable dynamic resource mechanism in twisted.web
EndpointCallable = typing.NewType("InstanceCallable",
                                  typing.Callable[
                                      [Request,
                                       typing.Optional[typing.Iterable],
                                       typing.Optional[typing.Dict],
                                       ], typing.Union[str, int]])

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
            #Catch inlineCallback's
            result = NOT_DONE_YET
        elif result is NOT_DONE_YET:
            pass #Reactor is holding open http channels if this isn't returned as is
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


class NullResource(resource.Resource):
    def render(self, request):
        return "TODO - Prevent this from showing"


class WebSite(server.Site):

    def __init__(self):
        self.routes = {}
        self.double_slash_warning = True

        self.no_resource_cls = NoResource
        self.jinja2_env = None

        server.Site.__init__(self, NullResource())


    def setTemplateDir(self, path):
        import jinja2

        if self.jinja2_env is None:
            self.jinja2_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(path)
                , autoescape=jinja2.select_autoescape(["html"])
            )
        else:
            raise RuntimeError(f"website.setTemplateDir already set {self.jinja2_env}")


    def render_template(self, template_name, **context):
        if self.jinja2_env is not None:
            return self.jinja2_env.get_template(template_name).render(**context)
        else:
            raise RuntimeError(f"render_template called without using setTemplateDir first")


    def setNoResourceCls(self, no_resource_cls):
        self.no_resource_cls = no_resource_cls

    def add(self, route_str):

        def decorator(func):
            action = ViewResource(route_str, func, self.double_slash_warning)
            self.routes[action.regex] = action

            return func

        return decorator

    def addResource(self, route_str:str, new_resource:resource.Resource) -> resource.Resource:
        """
            To allow for static directory support and or use of native Twisted resources

        :param route_str: str A valid regex pattern that is converted to re.compile for routing
        :param resource: twisted.web.resource.Resource
        :return: twisted.web.resource.Resource
        """
        if isinstance(route_str, str):
            route_str = route_str.encode()

        self.resource.putChild(route_str, new_resource)
        return new_resource

    def getResourceFor(self, request):

        str_request_path = request.path.decode()

        for path_regex, web_resource in self.routes.items():
            if path_regex.match(str_request_path) is not None:
                return web_resource
        else:
            # Routing failed with regex, default back to twisted.web's default routing system
            resrc = server.Site.getResourceFor(self, request)

        if isinstance(resource, NullResource):
            return self.no_resource_cls()
        else:
            return resrc


website = WebSite()
add = website.add
