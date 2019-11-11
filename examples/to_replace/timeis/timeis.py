
import time
import webbrowser

from txweb import Site as Site
from txweb import expose



from twisted.web.static import File
from twisted.internet import reactor, defer
from twisted.web.server import NOT_DONE_YET


class Root(object):

    index = File("./views/index.html")

    @expose
    def whatnow(self, request):

        return f"It is currently {time.time()}"


def run():
    reactor.listenTCP(8080, Site(Root()))
    reactor.callLater(3, webbrowser.open, "http://127.0.0.1:8080/" )
    reactor.run()

if __name__ == '__main__':
    print("Starting")
    run()
