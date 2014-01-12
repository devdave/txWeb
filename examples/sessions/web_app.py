
import time

from txweb import CSite as Site
from txweb import expose
from txweb.sugar.filters import json_out

from twisted.web.static import File
from twisted.internet import reactor, defer
from twisted.web.server import NOT_DONE_YET
from twisted.application import service, internet

from user import IWebUser
from user import WebUser

from txweb.sugar.reloader import ModuleReloader


class Root(object):




    index       = File("./html/home.html")
    app       = File("./app/")

    def _prefilter(self, request, resource):
        user = request.getSession(IWebUser)
        request.user = user
        if user.name == None:
            request.setHeader("x-is_new","1")
        print "Prefilter!"

    @expose
    @json_out
    def login(self, request):
        if request.args.name:
            request.user.name = request.args.name

        return {"success": request.user.name is not None, "name": request.user.name}
