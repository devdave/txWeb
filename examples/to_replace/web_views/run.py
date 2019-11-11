from txweb.web_views import website

from twisted.application import service, internet as app_internet
from twisted.web import static, server

from twisted.internet import reactor
from twisted.internet import threads
from twisted.web.server import NOT_DONE_YET
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web import static
from twisted import application

import time

import jinja2



@website.add("/")
def index(request):
    return request.site.render_template("home.html", title="Home page", routes=request.site.routes)


@website.add("/hello")
def helo(request):
    return b"Hello World"

@website.add("/safe_str")
def returns_unicode(request):
    return "Hello world! this was a &LT;str&GT;"

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


static_resource = website.addResource("static", static.File("./static/"))


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

@website.add("/argument/<name:str>")
def print_argument(request, name):
    return name

@website.add("/argument/foo/<number:int>")
def print_number(request, number):
    return number

PORT = 8080

def main():
    import sys
    from twisted.python import log
    log.startLogging(sys.stdout)
    website.setTemplateDir("./templates")
    reactor.listenTCP(PORT, website)
    reactor.run()


if __name__ == '__main__':
    from txweb.sugar.reloader import reloader
    reloader(main)
else:
    application = service.Application("web_views")
    website.setTemplateDir("./templates")
    web_service = app_internet.TCPServer(PORT, website)
    web_service.setServiceParent(application)