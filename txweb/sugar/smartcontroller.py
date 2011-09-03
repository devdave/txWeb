
import inspect
from collections import OrderedDict
from functools import wraps



class ControllerMethodDecorator(object):
    def __init__(self, directives):
        #Todo, do I need OrderedDict anymore?
        self.directives = OrderedDict(directives)
    
    
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
                if name[0:2] in ("r_","u_","a_"):
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
                    
                if name.startswith("a_"):
                    kwargs[name] = request.args.get(name[2:], default)                    
                    
                if name.startswith("u_"):
                    try:
                        kwargs[name] = postpath.pop(0)                        
                    except IndexError:
                        kwargs[name] = None
                        
            return f(inst, request, *args, **kwargs)
            
        return decorator

class SmartController(type):
    
    def __new__(mcs, clsname, bases, cdict):
        
        #Allow for application level override for the default decorator
        Decorator = cdict.get("__metamethoddecorator__", ControllerMethodDecorator)
            
        
        #Step 1 catch all methods prefixed with action_
        for name in cdict.iterkeys():
            if ( inspect.ismethod(cdict[name]) or inspect.isfunction(cdict[name]) ) and name.startswith("action_"):
                cdict[name[7:]] = cdict[name]
                del cdict[name]
                name = name[7:]
                cdict[name].exposed = True
            
            if hasattr(cdict[name], "exposed"):
                directives = Decorator.GetDirectives(cdict[name])
                if directives != False:
                    cdict[name] = Decorator(directives)(cdict[name])
                    
        
        return type.__new__(mcs, clsname, bases, cdict)
                
                