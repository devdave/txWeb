
from twisted.web import resource

def expose(target):
    """
        A simple decorate to add the .exposed attribute
    """
    target.exposed = True
    return target
    
    
class OneTimeResource(resource.Resource):
    """
        Monkey patch to avoid rewriting more of twisted's lower web
        layer which does a fantastic job dealing with the minute details
        of receiving and sending HTTP traffic.
        
        func is a callable and exposed property in the Root OO tree
    """
    def __init__(self, func, parent = None):
        self.func = func
        self.parent = parent
        
    def render(self, request):
        #Here would be a fantastic place for a pre-filter        
        if self.parent is not None:
            if hasattr(self.parent, "_prefilter"):
                try:
                    self.parent._prefilter(request)
                except Exception as e:
                    #TODO hook for overriding default request should go here
                    raise e
        
        response = self.func(request) #pragma: no cover
        if self.parent is not None:
            if hasattr(self.parent, "_postfilter"):
                try:
                    result = self.parent._postfilter(request, response)
                    if result is not None:
                        response = result
                except Exception as e:
                    #TODO
                    raise e
                
        return response
        
    