#Module level
from util import OneTimeResource
#Twisted level
from twisted.web import server, resource
from twisted.web.resource import ErrorPage, ForbiddenResource, NoResource

import copy

class Site(server.Site):
    """
        A monkey patch that short circuits the normal
        resource resolution logic @ the getResourceFor point
        
    """
        
                    
    def routeRequest(self, request):
        """
            Traverses the root controller and returns the first callable or Resource that
            matches the provided request.path
            :param request is a twisted.web.request object
            
            ex. Given a path like '/foo/test/x' it would match a OO graph of root.foo.test.x or the first callable
                element
            
            
            
        """
        
        isExposed  = lambda entity : getattr(entity, "exposed", False)
        isResource = lambda entity : callable(getattr(entity, "render", None))
        #TODO safe to assume if it's a resource that it should be exposed
        isAction = lambda entity : ( isExposed(entity) and callable(entity) ) or ( isResource(entity) )
            
            
        
        action = None
        response = None
        
        root = parent = self.resource
        defaultAction = getattr(root, "__default__", None ) or NoResource()
        
        endedWithSlash = request.path[-1] == "/"
        
        path = request.path
        if path.startswith("/"):
            path = path[1:]
            
        path = path.split("/")
        
        
        
        
        for i in range(len(path)):
            element = path[i]
            
            parent = root
            root = getattr(root, element, None)
            request.prepath.append(element)
            
            if root is None:
                """
                    if root has nulled out, check to see if the last element in the path was a controller
                    AND if so check for an index attribute that is callable or resource 
                """
                if request.path.endswith("/"):
                    if hasattr(parent, "index") and isAction(getattr(parent, "index")):
                        action = getattr(parent, "index")                    
                break
            
            if hasattr(root, "__default__") and isAction(getattr(root, "__default__")):
                #Check for a catchall default action
                defaultAction = getattr(root, "__default__")
                
                
            if element.startswith("_"):
                #500 simplistic security check
                return ErrorPage(500, "Illegal characters", "URI segments cannot start with an underscore")
                break #pragma: no cover
            
            if isAction(root):
                action = root
                request.postpath = path[i+1:]
                if isResource(root):
                    if len( path[i+1:] ) > 0:
                        childPath = request.postpath[:]
                        while childPath:
                            sub = childPath.pop(0)
                            action = action.getChild(sub, request)
                
                break
            
            
       
                
        
        if action is None:
            action = defaultAction or NoResource()
           
                
        return action if isResource(action) else OneTimeResource(action)
       
                
                
        
    def getResourceFor(self, request): #pragma: no cover
        request.site = self
        request.sitepath = copy.copy(request.prepath)
        resource = self.routeRequest(request)
        self.prefilter(request, resource)
        return resource
        
        
    def prefilter(self, request, resource):
        pass
    
    def postfilter(self, response):
        pass    