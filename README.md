Twisted Web extension
=====================

   A routing extension to twisted.web.
   
Philosophy & goals
---------------
The primary goal is to avoid re-inventing the wheel as much as possible when it comes to what Twisted.web has to offer.  That said I was a big fan
of Pylons and then still a devoted fan of CherryPy, but when dealing with asyncronous problems or when you need to connect http to some other protocol,
twisted is the only game in town.

As far as design/features go, txWeb is designed with the idea of progressive enhancement in mind.  All you need to use txWeb in a project is
core.Site and a graph of simple user defined objects, decorated with .expose = True on the appropriate methods.  Sesssion/Input/ HTTP action are
left to the user to decide what is or isn't valid.
    

Basic usage
----------------

```Python
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
           Proof of concept example of holding a response open ( for comet or polling JSON )
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
```

127.0.0.1/hello   calls Root->hello

127.0.0.1/sub/here calls SubPage->here


Mixed traditional usage
-----------------------

```Python
from txweb import Site, expose
from twisted.internet import reactor
from twisted.web.static import File

Class Root(object):
    
    index = File("path/2/index.html")
    js    = File("path/2/js/")

```


A call to / OR /index would return the body of path/2/index.html while /js/someFile.js could result in rendering the contents of the respective file or
a 404/500 if the file doesn't exist.   Additionally, just calling /js/ would resolve to a DirectoryLister resource instead.



Sugar
---------------------

And entering into quasi unstable territory would be my experiments with python metaclassing.

```Python
from txweb import Site, expose
from twisted.internet import reactor
from twisted.web.static import File
from txweb.sugar.smartcontroller import SmartController


class Root(object):
    __metaclass__ = SmartController
    """
        SmartController rewrites all methods that start with action_:name: to :name: then decorates them with the ActionMethodDecorator
           the __doc__ is as follows
        
            For methods with specially prefixed arguments like u_, a_, and r_
            extracts the appropriate value from different sources.
            u_ is a positional argument, the first u_ argument equals to request.postpath[0] and so on.  If missing or empty a u_ argument defaults to None
            a_ is a named argument where a_:name: equals request.args.get(name, [default])[0]
            al_ is a named argument where al_:name: equals request.args.get(name, default)
            c_ is a named argument where c_:name: equals a dictionary populated with all arguments that start with :name:
                so for a GET arg string like ?person.name=Dave&person.age=30&person.sex=Male would be c_person = Dict(name = DevDave, sex = Male, age = 30 )
            r_ is a named argument where r_:name: equals getattr(request, name, default = None)
    """
    
    
    def action_foo(a_name = None):    
        name = a_name if a_name is not None else "Nobody"
        return "Hello %s" % name
    #GET /foo?name=DevDave
    #results in "Hello DevDave
    
    def action_bar(u_position1 = None, u_position2 = None ):
        return "%s and then %s" % (u_position1, u_position2)
    #GET /bar/Stop/Go
    #results in "Stop and then Go"
    #GET /bar/Go/Stop
    #would result in "Go and then Stop"
    
    
    def action_blah():
    #UNTESTED but should work
        self.request.setHeader("Content-Type", "application/json")
        return dict(foo = Name, bar = "123")
    # ideally should create a HTTP response that jQuery will recgonize as JSON and received the JSON object {"foo":}
```

An additional overload idea would be methods prefixed with json_ that would automatically set the content-type response header  to 'application/json' and
then run the return from such a method through json.dumps.   The idea for the SmartController came about from a conversation at a bar with a friend
who was telling me about Grails and how classes prefix'd with Controller_ would automatically be decorated with helper/support methods to flesh out a simple class
without worrying about dependancies at development time.



Package future & unit-tests
---------------------------

Three of my personnel successfull pet projects use txWeb extensively and its through
issues discovered in these pets that txWeb is continued to be improved.  That said I think a
superset project maybe in order for more advanced features, leaving txWeb focused solely on
improving the routing logic.

At the moment coverage is showing almost everything is above 85% or better 100% coverage.  Ideally I'd like
to go back over the tests in place and clean them up as they're somewhat of a mess but that will probably happen
when I'm in a really good mood and want a reason to hate my past self for laziness.