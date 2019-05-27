#txWeb
from .util import OneTimeResource
from .util.is_a import isAction
from .util.is_a import isExposed
from .util.is_a import isResource

#Twisted
from twisted.web import server
from twisted.web.resource import NoResource

#stdlib
from collections import OrderedDict
import re

"""
    Routing overview:

    twisted.reactor recieves a new call, which is delegated by twisted.web...Site to twisted.web Request
    The request calls Site.getResourceFor(request)
        ***txweb start's here
        action = txweb.Site.getResourceFor -> routeRequest
        action can be either OneTimeResource or any valid TwistedWebRequest



"""
class CSite(server.Site):
    """
        Instead of walking along the object-graph looking for a match, build
        out a precomputed lookup table.
    """

    def __init__(self, resource, logPath=None, timeout=60*60*12):

        super().__init__(resource, logPath=logPath, timeout=timeout)
        # server.Site.__init__(self, resource, logPath, timeout)
        self.object_graph = self._compute_path(self.resource, "")

    def _compute_path(self, parent, path):


        graph = OrderedDict()
        # print parent, path

        if hasattr(parent, "index"):
            graph[re.compile("^%s/$" % path) ] = parent.index


        for name in dir(parent):
            if name.startswith("_"):
                continue

            obj = getattr(parent, name)

            if isAction(obj):
                node_body = "%s/%s" % (path, name,)
                if isExposed(obj):
                    graph[re.compile("^%s$" % node_body)] = obj
                elif isResource(obj):
                    graph[re.compile("^%s/?(.*)" % node_body)] = obj

            elif obj:
                graph.update(self._compute_path(obj, "%s/%s" % (path, name,)))

        return graph


    def routeRequest(self, request):

        action = None
        url_match = None
        str_request_path = request.path.decode()
        for url_regex, candidate in self.object_graph.items():
            url_match = url_regex.match(str_request_path)
            if url_match:
                action = candidate
                break


        if action is None:
            return NoResource()
        else:
            #Last step is to see what was found, if the target was a resource, we're done
            #For now, assuming only ^url/2/resource(.*)$ regexs are used for resources!

            if isResource(action):
                url_groups = url_match.groups()
                if url_groups:
                    childPath = url_match.groups()[0].split("/")
                    while childPath:
                        action = action.getChild(childPath.pop(0), request)

                return action

            else:
                return OneTimeResource(action)