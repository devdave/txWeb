"""
    This has become less a syntactic sugar addon as a heavily
    decorated wedding cake made of carmalized sugar.

    A high level overview:
        Controller classes define SmartController as their metaclass
            SmartController's __new__ then takes over.

"""

import inspect
from collections import OrderedDict
from collections import namedtuple
from functools import wraps
import attr

@attr.s
class AMDirectives(object):

    path_elements = attr.ib(default=attr.Factory(list))
    alist = attr.ib(default=attr.Factory(list))
    afirst = attr.ib(default=attr.Factory(list))
    prefixed = attr.ib(default=attr.Factory(dict))
    request_attrs = attr.ib(default=attr.Factory(list))
    is_method = attr.ib(default=False)

@attr.s
class AMParam(object):

    signature = attr.ib()

    @property
    def name(self):
        return self.signature.name
        
    @property
    def str_name(self):
        return self.signature.name.split("_",1)[1]

    @property
    def byte_name(self):
        return self.str_name.encode()

    @property
    def default(self):
        return None if self.signature.default == self.signature.empty else self.signature.default

    def fetch(self, src):
        if isinstance(src, dict):
            val = src.get(self.byte_name, self.default)
        else:
            val = getattr(src, self.str_name, self.default)

        if self.signature.annotation is not self.signature.empty and val != self.default:
            target = self.signature.annotation
            if isinstance(val, bytes) and target is str:
                val = val.decode()
            else:
                val = target(val)

        return val

    def fetch_first(self, src):
            val = self.fetch(src)
            return val[0] if isinstance(val, list) else val


def FindDirectives(method):
    """
        Builds a parameter list in the format dict(method_keyword_argument = [None|default value])
        If none of the parameters have a matching prefix, returns False
    """
    spec = inspect.signature(method)
    directives = AMDirectives()

    if ["self", "request"] == [x for x in spec.parameters]:
        directives.is_method = True
    elif len(spec.parameters) == 1 and "request" in spec.parameters:
        directives.is_method = False
    else:
        for param_name, param in spec.parameters.items():

            if param_name.find("_") == -1:
                continue

            prefix, name = param_name.split("_")
            if prefix in ['a', 'al', 'c', 'r']:
                if prefix == "a":
                    directives.afirst.append(AMParam(param))
                elif prefix == "al":
                    directives.alist.append(AMParam(param))
                elif prefix == "c":
                    directives.prefixed[param_name] = AMParam(param)
                elif prefix == "r":
                    directives.request_attrs.append(param_name)

    return directives

def ActionDecorator(src_func):
    """
        For methods with specifically prefixed arguments
        extracts the appropriate value from different sources.

        a_ is a named argument where a_:name: equals request.args.get(name, [default])[0]

        al_ is a named argument where al_:name: equals request.args.get(name, default)

        c_ is a named argument where c_:name: equals a dictionary populated with all arguments that start with :name:
            so for a GET arg string like ?person.name=Dave&person.age=30&person.sex=Male would be c_person = Dict(name = DevDave, sex = Male, age = 30 )

        r_ is a named argument where r_:name: equals getattr(request, name, default = None)
    """

    directives = FindDirectives(src_func)

    @wraps(src_func)
    def decorator(*args, **kwargs):

        #args could be cls, request, self,request, or just request
        request = args[-1]
        # assert hasattr(request, "get"), f"Unexpected param {request} in \n{dir(request)}\n"

        for param in directives.afirst:
            kwargs[param.name] = param.fetch_first(request.args)

        for param in directives.alist:
            kwargs[arg_name.name] = param.fetch(request.args)

        for prefix_name, default_value in directives.prefixed.items():

            prefixed_items = {}
            for request_arg_name, value in request.args.items():
                _, property_name = request_arg_name.split(b"_", 1)

                if request_arg.name.startswith(name):
                    prefixed_items[property_name[len(name):]] = value

            kwargs[prefix_name] = prefixed_items

        for prefixed_named in directives.request_attrs:
            _, attr_name = prefixed_named.split("_",1)
            kwargs[prefixed_named] = getattr(request, attr_name, None)

        return src_func(*args, **kwargs)

    return decorator

class SmartController(type):
    """
        Spins through a classes defined attributes looking for any function/method that has
        been decorated with .exposed = True OR any method/function with a prefix of action_

        If prefixed with action_, the target is stripped of the prefixed and decorated with .exposed
        if .exposed = True then a simple decorator is applied to remove the request variable and reassign it
        to the method's class instance.
        Furthermore ActionMethodDecorator or a child class is used to manage special prefixed arguments like u_, a_, p_, r_
    """
    def __new__(mcs, clsname, bases, cdict):

        #Allow for application level override for the default decorator
        decorator = cdict.get("__metamethoddecorator__", ActionDecorator)


        #Step 1 catch all methods prefixed with action_
        attributes = [x for x in cdict.keys() if x.startswith("action_") == True]

        for name in attributes:
            _, new_name = name.split("_",1)
            obj = cdict[name]
            if ( inspect.ismethod(obj) or inspect.isfunction(obj) ):
                setattr(obj, "exposed", True)
                cdict[new_name] = decorator(obj)
                del cdict[name]



        return type.__new__(mcs, clsname, bases, cdict)
