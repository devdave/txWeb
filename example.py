#App level
from txweb import Site, expose
#twisted
from twisted.web import server, resource
from twisted.internet import reactor
from twisted.web.static import File

from os.path import abspath, dirname, join

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
        """ /pagetwo/index """
        return "Hello From PageTwo index!"
        

rootFile = lambda filename : abspath(join(dirname(__file__), filename))
        
class Root(object):
    
    @expose
    def index(self, request):
        """
            Will handle both / and /index paths
        """
        return "Hello From Index!"
    
    @expose
    def __default__(self, request):
        """
            Unless overriden further down, this will catch all 404's
        """
        return "I Caught %s " % request.path
    
    pageone = PageOne()
    pagetwo = PageTwo()
        
    readme  = File(rootFile("README.md"))
    license = File(rootFile("txweb/LICENSE.txt"))
        
reactor.listenTCP(80, Site(Root()) )
reactor.run()


