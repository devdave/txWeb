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

