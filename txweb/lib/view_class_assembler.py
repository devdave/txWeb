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
import typing as T
from collections import namedtuple
import inspect

from werkzeug.routing import Rule, Submount

from txweb.util.basic import get_thing_name
from ..resources import ViewFunctionResource, ViewClassResource



EXPOSED_STR = "__exposed__"
EXPOSED_RULE = "__sub_rule__"

PREFILTER_ID = "__PREFILTER_ID__"
POSTFILTER_ID = "__POSTFILTER_ID__"


def has_exposed(obj) -> bool:
    """
        Does the provided object have an exposed endpoint?

    Parameters
    ----------
    obj: An instance of a View class with exposed members OR a render method

    Returns
    -------
    True if any method/function has been decorated with @texas.expose
    """
    return any([
        True
        for m in getattr(obj, "__dict__", {}).values()
        if inspect.isfunction(m) and hasattr(m, EXPOSED_STR)
    ])


# def is_exposed(attribute):
#     """
#         Is the provided callable/thing set as exposed?
#     :param attribute:
#     :return:
#     """
#     return has_exposed(attribute)


def is_viewable(attribute) -> bool:
    """
        Check if whatever this is, it is callable and has been marked as expose'd

    Parameters
    ----------
    A callable that has been expose'd

    Returns
    -------
    True if conditions have been met.

    """
    is_valid_callable = inspect.ismethod(attribute) \
                        or inspect.isfunction(attribute) \
                        or inspect.isgenerator(attribute) \
                        or inspect.iscoroutine(attribute) \
                        or inspect.iscoroutinefunction(attribute)

    return has_exposed(attribute) and is_valid_callable


def is_renderable(kls):
    """
        Does a class definition have a valid render method/function
        Generally checked if it has no exposed methods.

    Parameters
    ----------
    A potential view class

    Returns
    -------
    True if it has a renderable method (render or render_{HTTP REQUEST METHOD[POST, GET, HEAD, PUT, etc])
    """
    return \
        any([
            hasattr(kls, render_name)
            for render_name in ['render', 'render_get', 'render_post', 'render_put', 'render_head']
        ]) \
        or has_exposed(kls)


ExposeSubRule = namedtuple("ExposeSubRule", "method_name,route,route_kwargs")


def expose(route, **route_kwargs):
    """
        Decorator to set the exposed method's routing url and tag it with the exposed sentinel attribute

    Parameters
    ----------
    route: str
    route_kwargs: arguments intended to be passed on to werkzeug routing logic

    Returns
    -------
    T.Callable[[func], func] - a decorating function to set the exposed attribute and append routing arguments
    """
    def processor(func):
        setattr(func, EXPOSED_STR, True)
        setattr(func, EXPOSED_RULE, ExposeSubRule(func.__name__, route, route_kwargs))
        return func

    return processor


def set_prefilter(func):
    """
    decorator used to mark a class method as a prefilter for the class.

    Parameters
    ----------
    func: a valid prefilter callable

    Returns
    -------
    The same callable as was passed in as an argument
    """
    setattr(func, PREFILTER_ID, True)
    return func


def set_postfilter(func):
    """
    decorator used to mark a class method as a post filter for a class.

    Parameters
    ----------
    func - a valid postfilter callable

    Returns
    -------
    callable - the same function that was passed in as an argument

    """
    setattr(func, POSTFILTER_ID, True)
    return func


ViewAssemblerResult = namedtuple("ViewAssemblerResult", "instance,rule,endpoints")


def find_member(thing, identifier: str) -> T.Union[T.Callable, bool]:
    """
        Utility to search every member of an object for the provided `identifier` attribute

    Parameters
    ----------
    thing: an instance of a view class

    Returns
    -------
    The first matching instance method or attribute to have the `identifier` attribute
    """
    for _, member in inspect.getmembers(thing, lambda v: hasattr(v, identifier)):
        return member

    return False


def view_assembler(prefix: str,
                   kls,
                   route_args: T.Dict[str, T.Union[str, T.List[str]]]) -> T.Union[ViewAssemblerResult, None]:
    """
        Given a class definition, this instantiates the class, searches it for exposed
        methods and pre/post filters

            if it has no exposed methods,
                and builds a ViewAssemblerResult which contains the instance, submount rules,
                and references to the endpoints.
            else it checks if the class def has a render/render_METHOD method.
            else it throws UnrenderableException

    Parameters
    ----------
    prefix: str
        The view classes' URL prefix
    kls: claasdef
        A view class definition
    route_args: dict
        a dictionary of arguments intended for the werkzeug URL routing library

    Raises
    ------
    EnvironmentError
        Throws this error if the class defintion is not a valid View class

    Returns
    -------
    A ViewAssemblerResult if `kls` is a view class or has a valid render method function.
    """
    # pylint: disable=R0914
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

        prefilter = find_member(instance, PREFILTER_ID)
        postfilter = find_member(instance, POSTFILTER_ID)

        for name, bound_method in attributes.items():

            sub_rule = getattr(bound_method, EXPOSED_RULE)  # type: ExposeSubRule
            bound_endpoint = get_thing_name(bound_method)
            rule = Rule(sub_rule.route, **sub_rule.route_kwargs, endpoint=bound_endpoint)

            endpoints[bound_endpoint] = ViewFunctionResource(bound_method, prefilter=prefilter, postfilter=postfilter)
            rules.append(rule)

        return ViewAssemblerResult(instance, Submount(prefix, rules), endpoints)

    elif is_renderable(kls):
        endpoint = get_thing_name(instance)
        rule = Rule(prefix, **route_args, endpoint=endpoint)
        endpoints[endpoint] = ViewClassResource(kls, instance)
        return ViewAssemblerResult(instance, rule, endpoints)

    else:
        raise EnvironmentError(f"{kls.__name__!r} is missing exposed method(s) or a render method")
