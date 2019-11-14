from txweb.resources import ViewFunctionResource
from txweb.errors import UnrenderableException

from collections import namedtuple
from werkzeug.routing import Rule, Submount
from txweb.util.basic import get_thing_name

import inspect


def has_exposed(obj):
    return any([
        True
        for m in getattr(obj, "__dict__", {}).values()
            if inspect.isfunction(m) and hasattr(m, "__exposed__")
    ])

def is_renderable(kls):
    return \
        any([
            hasattr(kls, render_name)
            for render_name in ['render','render_get','render_post','render_put','render_head']
        ]) \
        or has_exposed(kls)




ExposeSubRule = namedtuple("ExposeSubRule", "method_name,route,route_kwargs")
def expose(route,**route_kwargs):

    def processor(func):
        setattr(func, "__exposed__", True)
        setattr(func, "__subrule__", ExposeSubRule(func.__name__, route, route_kwargs))
        return func

    return processor

ViewAssemblerResult = namedtuple("ViewAssemblerResult", "instance,rule,endpoints")

def view_assembler(prefix, kls, route_args):
    endpoints = {}
    instance = None
    rules = []
    if has_exposed(kls):
        kls_args = route_args.pop("init_args", [])
        kls_kwargs = route_args.pop("init_kwargs", {})

        instance = kls(*kls_args, **kls_kwargs)
        exposed = [
            getattr(
                getattr(instance, m),
                "__sub_rule__"
            )
            for m, m_obj in instance.__dict__.items()
                if inspect.ismethod(m_obj) and hasattr(m_obj, "__exposed__")
        ]
        for sub_rule in exposed:
            bound_method = getattr(instance, sub_rule.name)
            bound_name = get_thing_name(bound_method)
            rule = Rule(sub_rule.route, **sub_rule.kwargs, endpoint=bound_name)
            endpoints[bound_name] = ViewFunctionResource(bound_method)
            rules.append(rule)
    elif is_renderable(kls):
        raise NotImplementedError()
    else:
        raise UnrenderableException(f"{kls.__name__!r} is missing exposed method(s) or a render method")

    return ViewAssemblerResult(instance, Submount(prefix, rules), endpoints)

