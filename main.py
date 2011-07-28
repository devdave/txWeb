#App level
from txweb import Site, expose
#twisted
from twisted.web import server, resource
from twisted.internet import reactor



class PageOne(object):

    @expose
    def foo(self, request):
        return "Hello From PageOne Foo!"        
    
    @expose
    def delayed(self, request):
        def delayedResponse():
            request.write("I was delayed :( ")
            request.finish()
            
        reactor.callLater(5, delayedResponse)
        return server.NOT_DONE_YET
    
    
class PageTwo(object):

    @expose
    def index(self, request):
        return "Hello From PageTwo index!"
        
        
class Root(object):
    
    @expose
    def index(self, request):
        return "Hello From Index!"
    
    @expose
    def __default__(self, request):
        return "I Caught %s " % request.path
    
    pageone = PageOne()
    pagetwo = PageTwo()
        
        
reactor.listenTCP(80, Site(Root()) )
reactor.run()


