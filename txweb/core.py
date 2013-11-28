#TODO terrible module name
from util.is_a import isAction
from util.is_a import isExposed
from util.is_a import isResource

#Twisted level
from twisted.web import server
from twisted.web import resource
from twisted.internet import defer
from twisted.web.server import NOT_DONE_YET

#from twisted.web.resource import ErrorPage
#from twisted.web.resource import ForbiddenResource
from twisted.web.resource import NoResource


#stdlib
import re
import copy
from collections import OrderedDict
"""
    Routing overview:

    twisted.reactor recieves a new call, which is delegated by twisted.web...Site to twisted.web Request
    The request calls Site.getResourceFor(request)
        ***txweb start's here
        action = txweb.Site.getResourceFor -> routeRequest
        action can be either OneTimeResource or any valid TwistedWebRequest



"""



def expose(target):
    """
        A simple decorate to add the .exposed attribute
    """
    target.exposed = True
    return target


class ActionResource(resource.Resource):

    __slots__ = ['func', 'parent']
    exposed = True

    def __init__(self, func, parent = None, path = None):
        self.func = func
        self.parent = parent
        self.path = path

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __eq__(self, other):
        #TODO lookinto using decorator for this stuff!
        return other == self.func

    def redirectTo(self, request, *args, **kwargs):
        #TODO -
        request.redirect(self.path)
        request.finish()
        return NOT_DONE_YET

    def render(self, request):
        response = self.func(request)
        #If the response is a Deferred, tell the stack to stop pre-emptive
        # cleanup as the show's not over yet
        if isinstance(response, defer.Deferred):
            response = NOT_DONE_YET

        return response


class CSite(server.Site):
    """
        Instead of walking along the object-graph looking for a match, build
        out a precomputed lookup table.
    """

    def __init__(self, resource, logPath=None, timeout=60*60*12):
        #TODO I remember talking to exarkun or glyph on freenode but I have
        # no idea what the consensus was on using old style vs super
        # parent.method calls
        server.Site.__init__(self, resource, logPath, timeout)
        self.object_graph = self._compute_path(self.resource, "")

    def getResourceFor(self, request): #pragma: no cover
        """
            Copied from twisted.web.server.Site to allow for
            hijacking into txweb routing system.
        """
        request.site = self
        request.sitepath = copy.copy(request.prepath)
        return self.routeRequest(request)

    def _compute_path(self, parent, path):


        graph = OrderedDict()
        print parent, path

        if hasattr(parent, "index"):
            if isExposed(parent.index):
                parent.index = graph[re.compile("^%s/$" % path) ] = ActionResource(parent.index, path = "%s/" % path)
            else:
                graph[re.compile("^%s/$" % path) ] = parent.index



        for name in dir(parent):
            if name.startswith("_"):
                continue

            obj = getattr(parent, name)

            if isAction(obj):
                node_body = "%s/%s" % (path, name,)
                if isExposed(obj):
                    action = graph[re.compile("^%s$" % node_body)] = ActionResource(obj, path = node_body)
                    setattr(parent, name, action)


                elif isResource(obj):
                    graph[re.compile("^%s/?(.*)" % node_body)] = obj

            elif obj:
                graph.update(self._compute_path(obj, "%s/%s" % (path, name,)))

        return graph


    def routeRequest(self, request):

        action = None
        url_match = None
        for url_regex, candidate in self.object_graph.items():
            url_match = url_regex.match(request.path)
            if url_match:
                action = candidate
                break


        if action is None:
            return NoResource()

        #Last step is to see what was found, if the target was a resource, we're done
        #For now, assuming only ^url/2/resource(.*)$ regexs are used for resources!

        if isResource(action):
            url_groups = url_match.groups()
            if url_groups:
                childPath = url_match.groups()[0].split("/")
                while childPath:
                    action = action.getChild(childPath.pop(0), request)

        return action
