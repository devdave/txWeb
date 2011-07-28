Twisted Web extension
=====================

   A monkey patched hack of an extension to twisted.web.
   

Example usage
----------------


from txweb import Site, expose
from twisted.internet import reactor
from twisted.web.server import NOT_DONE_YET

class Root(object):

    @expose
    def hello(self, request):
        return " world!"
        
    @expose
    def delayed(self, request):
        """
           Example of holding a response open ( for comet or polling JSON )
        """
        def delayedResponse():
            request.write("I was late")
            request.finish()
            
        reactor.callLater(5, delayedResponse)
        return NOT_DONE_YET
        
    sub = SubPage()
        
class SubPage(object):
    
    @expose
    def here(self, request):
        return "there!"
        

reactor.listenTCP(Site(Root()))
reactor.run

127.0.0.1/hello   calls Root->hello
127.0.0.1/sub/here calls SubPage->here
