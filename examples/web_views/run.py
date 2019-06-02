from txweb.web_views import website

from twisted.application import service, internet as app_internet
from twisted.web import static, server

from twisted.internet import reactor
from twisted.internet import threads
from twisted.web.server import NOT_DONE_YET
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted import application

import jinja2

import time

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader("./templates")
    , autoescape=jinja2.select_autoescape(["html"])
)

def render(template_name, **context):
    return env.get_template(template_name).render(**context)



@website.add("/")
def index(request):
    routes = website.routes
    return render("home.html", title="Home page", routes=routes)

@website.add("/hello")
def helo(request):
    return b"Hello World"


@website.add("/delayed")
def timed(request):

    def callme():
        request.write(b"It's later!")
        request.finish()

    def halfway():

        request.write(b"Almost done")
        request.write(b"<br>")

    reactor.callLater(2, halfway)
    reactor.callLater(5, callme)

    return NOT_DONE_YET


def sleepfor5seconds(sleeptime):

    print("Going to sleep")
    time.sleep(sleeptime)
    print("Sleep finished")

    return time.time()

@website.add("/deferred")
@inlineCallbacks
def stepbystep(request):

    print("Calling a sleeping thread")
    result = yield threads.deferToThread(sleepfor5seconds, 2)
    print(f"Got result {result}")
    request.write(str(result).encode() + b"<br>")
    result = yield threads.deferToThread(sleepfor5seconds, 2)
    request.write(b"Finished @ ")
    request.write(str(result).encode())


    request.finish()
    print("Finished!")

PORT = 8080

def main():
    import sys
    from twisted.python import log
    log.startLogging(sys.stdout)

    reactor.listenTCP(PORT, website)
    reactor.run()

if __name__ == '__main__':
    from txweb.sugar.reloader import reloader
    reloader(main)
else:
    application = service.Application("web_views")
    web_service = app_internet.TCPServer(PORT, website)
    web_service.setServiceParent(application)