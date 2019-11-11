
from txweb.web_views import WebSite

from twisted.web.static import File
from twisted.internet import reactor, defer
from twisted.web.server import NOT_DONE_YET

Site = WebSite()

Site.add_resource("/", File("./index.html"))



def main():
    reactor.listenTCP(8123, Site)
    reactor.run()


if __name__ == "__main__":
    main()
