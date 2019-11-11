

from txweb import Site, expose
from twisted.web.static import File
from twisted.internet import reactor, defer
from twisted.web.server import NOT_DONE_YET
from twisted.internet import protocol

import time
import pathlib as pl
import cgi
import tempfile

HERE = pl.Path(__file__).resolve().parent()

class GifMaker(protocol.ProcessProtocol):
    pass

class WebRoot(object):

    def __init__(self):
        self.active_worker = None
        self.last_status = None

    def storefile(self, request):
        headers = request.getAllHeaders()
        video = cgi.FieldStorage(
            fp = request.content,
            headers = headers,
            environ = {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": headers['content_type']
            }
        )
        tempfile = tempfile.NamedTemporaryFile(suffix="mp4",dir=str(HERE/"temp"),delete=False)
        tempfile.write(img["upload"].value)
        tempfile.close()
        return pl.Path(tempfile)
        
        
        
        

    @expose
    def do(self, request):
        #Recieve a file
        #Save to temp
        tempfile = self.storefile(request)
        #process

        return NOT_DONE_YET

    @expose
    def fetch(self, request):
        pass



def run():
    reactor.listenTCP(8080, Site(WebRoot(ZeHub())))
    reactor.run()

if __name__ == '__main__':
    run()
