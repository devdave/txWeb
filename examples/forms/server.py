from txweb.web_views import WebSite
from txweb.util.reloader import reloader

from twisted.internet import reactor
from twisted.python import log

import sys

site = WebSite()

index = site.add_file("/", "./index.html")

@site.add("/simple", methods=["POST"])
def handle_simple_form(request):
    buffer = \
    f"""
    {request.args[b'word']}<br>
    {request.args[b'checked']}<br>
    """
    return buffer

@site.add("/complicated", methods=["POST"])
def handle_complicated_form(request):
    debug = 1
    buffer = \
    f"""
    
    <h2>Raw request</h2>
    <pre>{request.content.read().decode("utf-8")}</pre>
    <h2>Form results</h2>
    {request.args.get(b'word')}<br>
    <br>
    {request.args.get(b'checked','off')}<br>
    <br>
    <pre>
    {request.args[b'a_file'][0].decode("utf-8")}
    </pre>
    """
    return buffer



def main():
    log.startLogging(sys.stdout)
    reactor.listenTCP(8345, site)
    reactor.run()


if __name__ == "__main__":
    reloader(main)
