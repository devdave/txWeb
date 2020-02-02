"""
    Provides processing for View classes which connects multiple bound methods across multiple ViewFunction resources

    @app.add_class("/thing")
    class ViewContainer(object):
        def __init__(self):
            self.count = 0

        @app.expose("/add", methods=["POST"]) # /thing/add
        def handle_add(self, request):
            self.count = request.form.get('number', type=int, default=0)

        @app.expose("/add/<int:number>", methods=["GET"])  #  /thing/add/123
        def handle_get_add(request, number):
            self.count += number

        @app.expose("/show", methods=["GET"]) # /thing/show
        def handle_show(self, request):
            return compat.IntToBytes(self.count)

"""
from ..resources import ViewFunctionResource, ViewClassResource
from txweb.http_codes import UnrenderableException
from txweb.util.basic import get_thing_name

from collections import namedtuple
import inspect

from werkzeug.routing import Rule, Submount



import inspect

EXPOSED_STR = "__exposed__"
EXPOSED_RULE = "__sub_rule__"


def has_exposed(obj):
    return any([
        True
        for m in getattr(obj, "__dict__", {}).values()
        if inspect.isfunction(m) and hasattr(m, EXPOSED_STR)
    ])

def is_exposed(attribute):


    return has_exposed(attribute, EXPOSED_STR) and is_valid_callable

def is_viewable(attribute):
    is_valid_callable = inspect.ismethod(attribute) \
                        or inspect.isfunction(attribute) \
                        or inspect.isgenerator(attribute) \
                        or inspect.iscoroutine(attribute) \
                        or inspect.iscoroutinefunction(attribute)

    return is_exposed(attribute) and is_valid_callable


def is_renderable(kls):
    return \
        any([
            hasattr(kls, render_name)
            for render_name in ['render', 'render_get', 'render_post', 'render_put', 'render_head']
        ]) \
        or has_exposed(kls)


ExposeSubRule = namedtuple("ExposeSubRule", "method_name,route,route_kwargs")


def expose(route, **route_kwargs):

    def processor(func):
        setattr(func, EXPOSED_STR, True)
        setattr(func, EXPOSED_RULE, ExposeSubRule(func.__name__, route, route_kwargs))
        return func

    return processor


ViewAssemblerResult = namedtuple("ViewAssemblerResult", "instance,rule,endpoints")


def view_assembler(prefix, kls, route_args):
    endpoints = {}

    rules = []
    kls_args = route_args.pop("init_args", [])
    kls_kwargs = route_args.pop("init_kwargs", {})
    instance = kls(*kls_args, **kls_kwargs)

    if has_exposed(kls):

        attributes = {
            name: getattr(instance, name)
            for name in dir(instance)
            if name[0] != "_"
            and inspect.ismethod(getattr(instance, name))
            and hasattr(getattr(instance, name), EXPOSED_STR)
        }

        for name, bound_method in attributes.items():

            sub_rule = getattr(bound_method, EXPOSED_RULE)
            bound_endpoint = get_thing_name(bound_method)
            rule = Rule(sub_rule.route, **sub_rule.route_kwargs, endpoint=bound_endpoint)
            prefilter = getattr(instance, "_prefilter", None)
            postfilter = getattr(instance, "_postfilter", None)

            endpoints[bound_endpoint] = ViewFunctionResource(bound_method, prefilter=prefilter, postfilter=postfilter)
            rules.append(rule)

        return ViewAssemblerResult(instance, Submount(prefix, rules), endpoints)

    elif is_renderable(kls):
        endpoint = get_thing_name(instance)
        rule = Rule(prefix, **route_args, endpoint=endpoint)
        endpoints[endpoint] = ViewClassResource(kls, instance)
        return ViewAssemblerResult(instance, rule, endpoints)

    else:
        raise UnrenderableException(f"{kls.__name__!r} is missing exposed method(s) or a render method")
