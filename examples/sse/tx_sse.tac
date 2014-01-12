
import os
from txweb import CSite
from twisted.internet import reactor
from twisted.application import service
from twisted.application import internet
from web_app import Root
from ps_monitor import


from txweb.sugar.reloader import ModuleReloader

def getWebService():
    ModuleReloader.WatchThis(os.getcwd())
    webapp = CSite(Root())
    return internet.TCPServer(8080, webapp)

def getPsMonitor():
    psmon = PSMonitor(port = 7676, addr = '127.0.0.1')
    return internet.TimerService(10, psmon.step)

app = application = service.Application("demo txweb sse")

service = getWebService()
service.setServiceParent(application)
