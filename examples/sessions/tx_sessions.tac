
import os
from txweb import CSite
from twisted.internet import reactor
from twisted.application import service
from twisted.application import internet
from web_app import Root


from txweb.sugar.reloader import ModuleReloader

def getWebService():
    ModuleReloader.WatchThis(os.getcwd())
    webapp = CSite(Root())
    return internet.TCPServer(8080, webapp)


app = application = service.Application("demo txweb sessions")

service = getWebService()
service.setServiceParent(application)
