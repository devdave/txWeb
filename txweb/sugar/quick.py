import inspect
import functools
from .utils import fetch_first

class BaseAnnotatedHandler(object):
    pass


def annotated_router(func, sig):

    
    @functools.wraps(func)
    def decorator(*args, **keywords):


        return func(*args, **keywords)

    return decorator

def QArg(default_value=None):

    def decorator(request):
        return fetch_first(request, default_value)

    return decorator
    

def ReqAttr(required=False):

    def handler(request, arg_name):
        if required is False:
            return getattr(request, arg_name, None)

        return getattr(request, arg_name)



class QuickParam(type):

    def __new__(mcs, clsname, bases, cdict):

        is_callable = lambda thing: inspect.ismethod(thing) or inspect.isfunction(thing)

        #Step 1 catch all methods prefixed with action_
        methods = {x:cdict[x] for x in cdict.keys() if x.startswith("action_") and is_callable(cdict[x])}


        
        is_annotated = lambda x: is_callable(x) or inspect.isclass(x)


        for original_name, obj in methods.items():

            obj = cdict[original_name]
            _, final_name = original_name.split("_", 1)
            print(obj)
            obj_sig = inspect.signature(obj)

            if any(is_annotated(p.annotation) for p in obj_sig.parameters.values()):
                obj = annotated_router(obj, obj_sig)

            if original_name.startswith("action_"):
                _, new_name = original_name.split("_", 1)
                del cdict[original_name]
                setattr(obj, "exposed", True)
                cdict[new_name] = obj
            else:
                cdict[original_name] = obj
                
        return super().__new__(mcs, clsname, bases, cdict)
                
                
            
            
                
            
            
            


        return super().__new__(mcs, clsname, bases, cdict)

