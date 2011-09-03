
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
    def __init__(self, func):
        self.func = func
        
    def render(self, request):
        #Here would be a fantastic place for a pre-filter
        return self.func(request) #pragma: no cover
        #ditto here for a post filter
    