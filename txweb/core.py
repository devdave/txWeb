#Module level
from util import OneTimeResource
#Twisted level
from twisted.web import server, resource
from twisted.web.resource import ErrorPage, ForbiddenResource, NoResource


class Site(server.Site):
    """
        A monkey patch that short circuits the normal
        resource resolution logic @ the getResourceFor point
        
    """
    def checkAction(self, controller, name):
        """
            On success, returns a bound method from the provided controller instance
            else it return None
        """
        action = None
        if hasattr(controller, name):
                action = getattr(controller, name)
                if not callable(action) or not hasattr(action, "exposed"):
                    action = None
        
        return action
        
                    
    def routeRequest(self, request):
        """
            Traverses the root controller and returns the first callable or Resource that
            matches the provided request.path
            :param request is a twisted.web.request object
            
            ex. Given a path like '/foo/test/x' it would match a OO graph of root.foo.test.x or the first callable
                element
            
            
            
        """
        
        action = None
        response = None
        
        root = parent = self.resource
        defaultAction = self.checkAction(root, "__default__") or NoResource()
        
        path = request.path.strip("/").split("/")
        
        isExposed  = lambda entity : getattr(entity, "exposed", False)
        isResource = lambda entity : callable(getattr(entity, "render", None))
        #TODO safe to assume if it's a resource that it should be exposed
        isAction = lambda entity : ( isExposed(entity) and callable(entity) ) or ( isResource(entity) )
        
        
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
                    else:
                        action = defaultAction
                break
            
            if hasattr(root, "__default__") and isAction(getattr(root, "__default__")):
                #Check for a catchall default action
                defaultAction = getattr(root, "__default__")
                
                
            if element.startswith("_"):
                #500 simplistic security check
                return ErrorPage(500, "Illegal characters", "URI segments cannot start with an underscore")
                break
            
            if isAction(root):
                action = root
                request.postpath = path[i:]
                break;
            
            
                
        else:
            """
                According to coverage, tests never hit this entire block
                TODO next push eliminate
            """
            if action is None: 
                if root is not None and self.checkAction(root, "index"):
                    action = self.checkAction(root, "index")
                
        
        if action is None:
            action = defaultAction or NoResource()
           
                
        return action if hasattr(action, "render") else OneTimeResource(action)
       
                
                
        
    def getResourceFor(self, request):
        return self.routeRequest(request)