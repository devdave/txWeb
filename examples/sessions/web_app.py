
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

    app             = File("./app/")
    home_page       = File("./html/home.html")

    index           = home_page

