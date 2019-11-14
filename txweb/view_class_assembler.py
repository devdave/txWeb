ExposeSubRule = namedtuple("ExposeSubRule", "method_name,route,route_kwargs")
def expose(route,**route_kwargs):

    def processor(func):
        setattr(func, "__exposed__", True)
        setattr(func, "__subrule__", ExposeSubRule(func.__name__, route, route_kwargs))
        return func

    return processor

