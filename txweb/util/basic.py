
from twisted.web import resource
from twisted.internet import defer
from twisted.web.server import NOT_DONE_YET

def expose(target):
    """
        A simple decorate to add the .exposed attribute
    """
    target.exposed = True
    return target


def get_thing_name(thing: object) -> str:
    """
        Attempts to return a unique and informative name for thing

        Currently relies exclusively on __qualname__ as per https://www.python.org/dev/peps/pep-3155/

    """

    return getattr(thing, "__qualname__") #throws exception if it doesn't have __qualname__ property


class ActionResource(resource.Resource):

    __slots__ = ['func', 'parent']

    def __init__(self, func, parent = None):
        self.func = func
        self.parent = parent

    def render(self, request):

        response = self.func(request) #pragma: no cover

        if isinstance(response, str):
            response = response.encode()

        #If the response is a Deferred, tell the stack to stop pre-emptive
        # cleanup as the show's not over yet
        if isinstance(response, defer.Deferred):
            response = NOT_DONE_YET

        return response



class OneTimeResource(ActionResource):
    """
        Monkey patch to avoid rewriting more of twisted's lower web
        layer which does a fantastic job dealing with the minute details
        of receiving and sending HTTP traffic.

        func is a callable and exposed property in the Root OO tree
        :parent is an optional param that is usually the parent instance of Func and allows for pre/post filter methods
    """

    def render(self, request):

        #Here would be a fantastic place for a prefilter
        if self.parent is not None:
            if hasattr(self.parent, "_prefilter"):
                try:
                    self.parent._prefilter(request)
                except Exception as e:
                    #TODO hook for overriding default request should go here
                    raise e

        response = ActionResource.render(self, request)
        
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
