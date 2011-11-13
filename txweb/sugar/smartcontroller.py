"""
    This has become less a syntactic sugar addon as a heavily
    decorated wedding cake made of carmalized sugar.
    
    A high level overview:
        Controller classes define SmartController as their metaclass
            SmartController's __new__ then takes over.
    
"""

import inspect
from collections import OrderedDict
from functools import wraps


class ActionMethodDecorator(object):
    """
        For methods with specially prefixed arguments like u_, a_, and r_
        extracts the appropriate value from different sources.
        u_ is a positional argument, the first u_ argument equals to request.postpath[0] and so on.  If missing or empty a u_ argument defaults to None
        a_ is a named argument where a_:name: equals request.args.get(name, [default])[0]
        al_ is a named argument where al_:name: equals request.args.get(name, default)
        c_ is a named argument where c_:name: equals a dictionary populated with all arguments that start with :name:
            so for a GET arg string like ?person.name=Dave&person.age=30&person.sex=Male would be c_person = Dict(name = DevDave, sex = Male, age = 30 )
        r_ is a named argument where r_:name: equals getattr(request, name, default = None)
        
    """
    def __init__(self, directives):
        #Todo, do I need OrderedDict anymore?
        self.directives = OrderedDict(directives) if directives else {}
    
    
    @classmethod
    def GetDirectives(self, method):
        """
            Builds a parameter list in the format dict(method_keyword_argument = [None|default value])
            If none of the parameters have a matching prefix, returns False
        """
        spec = inspect.getargspec(method)
        try:
            name2default = zip(spec.args[-len(spec.defaults):], spec.defaults)
        except TypeError:
            #Should only happen in len(spec.defaults) where default is None
            return False
        else:
            for (name, default) in name2default:
                if name[0:2] in ("r_","u_","a_", "al_", "c_"):
                    return name2default
        
        #All test cases show this line isn't ever reached, still as a backup its here
        return False #pragma: no cover
        
    
    def __call__(self, f):
    
        @wraps(f)
        def decorator(inst, request, *args, **kwargs):
            
            postpath = request.postpath[:]            
            for name, default in self.directives.items():
                if name.startswith("r_"):
                    kwargs[name] =  getattr(request, name[2:], default)
                
                elif name.startswith("a_"):
                    kwargs[name] = request.args.get(name[2:], [default])[0]
                    
                elif name.startswith("al_"):
                    kwargs[name] = request.args.get(name[2:], [default])
                elif name.startswith("c_"):
                    #composite input
                    compositePrefix = name[2:]
                    #+1 to catch . or _
                    compositeLen = len(compositePrefix) + 1
                    data = dict()
                    for argname, value in request.args.items():
                        if argname.startswith(compositePrefix):
                            if isinstance(value, list):
                                subName = argname[compositeLen:].strip("[]");
                                
                                if len(value) > 1:                                    
                                    data[subName] = value
                                else:
                                    data[subName] = value[0]
                            else:
                                #I don't know what you are anymore
                                data[argname[compositeLen:]] = value
                            
                    kwargs[name] = data
                    del compositePrefix
                    del compositeLen
                    
                elif name.startswith("u_"):
                    try:
                        kwargs[name] = postpath.pop(0)                        
                    except IndexError:
                        kwargs[name] = default
            
            try:
                setattr(inst, "request", request)
                retval = f(inst, *args, **kwargs)
            finally:
                setattr(inst, "request", None)
            
            return retval
            
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
        Decorator = cdict.get("__metamethoddecorator__", ActionMethodDecorator)
            
        
        #Step 1 catch all methods prefixed with action_
        for name in cdict.keys():
            if ( inspect.ismethod(cdict[name]) or inspect.isfunction(cdict[name]) ) and name.startswith("action_"):
                cdict[name[7:]] = cdict[name]
                del cdict[name]
                name = name[7:]
                setattr(cdict[name], "exposed", True)
                
                #TODO unwind/compact ActionMethodDecorator to avoid this mess
                cdict[name] = Decorator(Decorator.GetDirectives(cdict[name]))(cdict[name])
                        
                
                    
                
                
            
        
        return type.__new__(mcs, clsname, bases, cdict)
                
                