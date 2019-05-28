from txweb.web_views import website
from twisted.internet import reactor
from twisted.internet import threads
from twisted.web.server import NOT_DONE_YET
from twisted.internet.defer import inlineCallbacks, returnValue

import time

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
    print(f"Got result {result}<br>")
    request.write(str(result).encode() + b"<br>")
    result = yield threads.deferToThread(sleepfor5seconds, 2)
    request.write(b"Finished @ ")
    request.write(str(result).encode())


    request.finish()
    print("Finished!")


def run():
    reactor.listenTCP(8080, website)
    reactor.run()


if __name__ == '__main__':
    run()