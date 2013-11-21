#Module level
from util import OneTimeResource
#TODO terrible module name
from util.is_a import isAction
from util.is_a import isExposed
from util.is_a import isResource

#Twisted level
from twisted.web import server
from twisted.web import resource
from twisted.web import util

from twisted.web.resource import ErrorPage
from twisted.web.resource import ForbiddenResource
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

class CBranch(object):
    """
        To simplify traversing/descending an object graph, make all branches
        required to be an child class of CBranch.
    """
    pass


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

    def _compute_path(self, parent, path):


        graph = OrderedDict()
        print parent, path

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
                    graph[re.compile("^%s.*" % node_body)] = obj

            elif obj:
                graph.update(self._compute_path(obj, "%s/%s" % (path, name,)))

        return graph


    def routeRequest(self, request):

        action = None
        for url_regex, candidate in self.object_graph.items():
            if url_regex.match(request.path):
                action = candidate
                break


        if action is None:
            return NoResource()
        else:
            #Last step is to see what was found, if the target was a resource, we're done
            if isResource(action):
                return action
            else:
                return OneTimeResource(action)


class Site(server.Site):
    """
        A monkey patch that short circuits the normal
        resource resolution logic @ the getResourceFor entry point

    """


    def routeRequest(self, request):
        """
            Traverses from the root controller, down through its children and returns the first callable or Resource that
            matches the provided request.path
            If there is no match, it will return NoResource

            :param request is a twisted.web.request instance


            ex. Given a path like '/foo/test/x' it would match a OO graph of root.foo.test.x or the first callable
            in that line.  so if root.root() has a method called test, then 'x' will be pushed into


        """
        action = None

        #self.resource is the Root controller object provided to Site.__init__(resource)
        root = parent = self.resource
        """
            defaultAction is a catch_all method that is set to intercept routing fallouts
            below the current parent.
            Example:

            Given
                a request path like "/foo/bar/something/something/

            and a Graph like

                class Bar:
                    pass

                class Foo:
                    bar = Bar()

                class Root:
                    def __default__(self, request):
                        return "Root default handler"

                    foo = Foo()


                Root.__default__ will end up being called

                if Foo had a __default__ method, it would be called instead
                if Bar had a __default__ method, then naturally it would be called

                The default action mechanism is the only planned means of supporting out of order routing
                like "/person/123/edit" where the desired action is to call Root.person.edit(<Request args={record_id:123} )
        """
        defaultAction = getattr(root, "__default__", None ) or NoResource()


        #crucial check because /foo/bar and /foo/bar/ should be treated as different ( former suggest Foo.<bound method bar> while the second Foo.<object instance bar>)
        endedWithSlash = request.path.endswith("/")
        path = request.path.strip("/").split("/")




        for i, element in enumerate(path):

            #For the first run through the loop, parent == root, but subsequent iterations parent will equal the Nth child of root
            parent = root
            root = getattr(root, element, None)
            request.prepath.append(element)

            if root is None:
                """
                    if root has nulled out, check to see if the last element in the path was a controller
                    AND if so check for an index attribute that is callable or resource
                """
                if endedWithSlash:
                    if hasattr(parent, "index") and isAction(getattr(parent, "index")):
                        action = getattr(parent, "index")
                break


            if hasattr(root, "__default__") and isAction(getattr(root, "__default__")):
                #Check for a catchall default action
                defaultAction = getattr(root, "__default__")


            if element.startswith("_"):
                #500 simplistic security check
                #There is already the exposed check, but this is a second security check to prevent calls to Root.__dict__ or such
                return ErrorPage(500, "Illegal characters", "URI segments cannot start with an underscore")
                break #pragma: no cover

            if isAction(root):
                action = root
                request.postpath = path[i+1:]
                if isResource(root):
                    """
                        NOTE:
                            For twisted.web a path like "/foo/bar/blah" translates to ["","foo","bar","blah"]
                            while "/foo/bar/blah/" == ["","foo","bar","blah",""] which is how Str.split works.
                            twisted.web's pathing logic depends on the prior result for Resource child delegation.
                            txweb meanwhile, doesn't.
                    """
                    if len( path[i+1:] ) > 0:
                        childPath = request.postpath[:]
                        while childPath:
                            sub = childPath.pop(0)
                            action = action.getChild(sub, request)
                    elif endedWithSlash:
                        #TODO need more unit-tests to clarify why I did this
                        #given foo = File("somePath/") and a path like "/foo/", expected twisted behavior is File to be given path of ""
                        action = action.getChild("", request)

                break







        if action is None:
            if endedWithSlash and hasattr(root, "index"):
                action = getattr(root, "index")

            #handles calls to child object attributes where they're at root.foo and url == "/foo" but should be "/foo/"
            elif not endedWithSlash and element in dir(parent) and element[0] != "_" and isinstance(getattr(parent, element), object):
                action = util.Redirect("%s/" % request.path)

        if action is None:
            action = defaultAction or NoResource()

        #Last step is to see what was found, if the target was a resource, we're done
        if isResource(action):
            return action
        #If action was a non-resource callable, bind the callable's parent to allow for pre/post filter logic in OneTimeResource
        elif parent is not None and isinstance(parent, object):
            return OneTimeResource(action, parent)
        else:
            #This isn't ideal but could be a result of Root having a __call__ method
            #Coverage in WebMud & PyProxy SSR both show this is never reached - placed on TODO as an Exception
            return OneTimeResource(action)



    def getResourceFor(self, request): #pragma: no cover
        """
            TODO should I add a try...catch here?
        """
        request.site = self
        request.sitepath = copy.copy(request.prepath)
        return self.routeRequest(request)
