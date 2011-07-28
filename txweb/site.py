#Module level
from .util import OneTimeResource
#Twisted level
from twisted.web import server

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
        action = None
        response = None
        
        root = parent = self.resource
        defaultAction = self.checkAction(root, "__default__")
        
        path = request.path.strip("/").split("/")
        
         
        
        for i in range(len(path)):
            element = path[i]
            
            parent = root
            root = getattr(root, element, None)
            request.prepath.append(element)
            
            if root is None:                
                break
            
            if self.checkAction(root, "__default__"):
                #Check for a catchall default action
                defaultAction = self.checkAction(root, "__default__")
                
                
            if element.startswith("_"):
                #500 simplistic security check
                action = lambda request: "500 URI segments cannot start with an underscore"
                break
                
            if callable(root) and hasattr(root, "exposed") and root.exposed == True:
                action = root
                request.postpath = path[i:] 
                break
            
            
                
        else:
            if action is None:
                if root is not None and self.checkAction(root, "index"):
                    action = self.checkAction(root, "index")
                
                
        #action = OneTimeResource(action) if action is not None else OneTimeResource(lambda request:"500 Routing error :(")
        if action is None:
            if defaultAction:
                action = defaultAction
            else:            
                action = lambda request:"404 :("
                
        return OneTimeResource(action)         

                
                
        
    def getResourceFor(self, request):
        return self.routeRequest(request)