
import time
import webbrowser

from txweb import Site as Site
from txweb import expose



from twisted.web.static import File
from twisted.internet import reactor, defer
from twisted.web.server import NOT_DONE_YET



class Root(object):

    landing_page    = File("./landing_page.html")
    home_page       = File("./home.html")
    register_page   = File("./register.html")

    @expose
    def index(self, request):
        # from dbgp.client import brk; brk("192.168.1.2", 9090)
        return "index"

    @expose
    def on_register(self, request):
        # from dbgp.client import brk; brk("192.168.1.2", 9090)
        if not request.args.get('name', False):
            return "Missing name"



def run():
    reactor.listenTCP(8080, Site(Root()))
    reactor.callLater(3, webbrowser.open, "http://127.0.0.1:8080/home" )
    reactor.run()

if __name__ == '__main__':
    run()
