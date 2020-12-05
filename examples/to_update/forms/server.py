from txweb.web_site import WebSite
from txweb.util.reloader import reloader

from twisted.internet import reactor
from twisted.python import log

import sys

site = WebSite()

index = site.add_file("/", "./index.html")

@site.add("/get_form", methods=["GET"])
def handle_get_args(request):
    return f"""
    {request.args.get('word')!r}<br>
    {request.args.get('number')!r}<br>
    {request.args.get('checked', False, type=bool)!r}<br>
    """

@site.add("/simple", methods=["POST"])
def handle_simple_form(request):
    buffer = \
    f"""
    {request.form.get('word')}<br>
    {request.form.get('checked')}<br>
    """
    return buffer

@site.add("/complicated", methods=["POST"])
def handle_complicated_form(request):
    debug = 1
    buffer = \
    f"""
    
    <h2>Raw request</h2>
    <dl>
        <dt>Content type</dt>
        <dd>{request.getHeader("content-type")}

        <dt>Content length</dt>
        <dd>{request.getHeader("content-length")}
    </dl>

    <textarea cols=80>{request.content.read().decode("utf-8")}</textarea>

    <h2>Form results</h2>
    <ol>
        <li>
            <label>Word</label>&nbsp;<span>{request.form.get('word')!r}</span>
        </li>
        <li>
            <label>Checked</label>&nbsp;<span>{request.args.get('checked','off')!r}</span>
        </li>
        <li><label>a_file</label><br>
            <textarea cols=80 rows=-1>
            {request.files['a_file'].stream.read().decode("utf-8")}
            </textarea>
        </li>   
    </ol>
    """

    return buffer



def main():
    log.startLogging(sys.stdout)
    site.displayTracebacks = True
    reactor.listenTCP(8345, site)
    reactor.run()


if __name__ == "__main__":
    reloader(main)
