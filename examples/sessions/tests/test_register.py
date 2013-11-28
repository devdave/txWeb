#pragma: no cover
from os.path import dirname, abspath, join
import nose
from nose.tools import eq_

import json

from txweb.core import CSite
from txweb.util.util_test import TestRequest
from user import IWebUser

from twisted.web.resource import ErrorPage
from twisted.web.resource import NoResource
from twisted.web.static import File
from twisted.web.server import NOT_DONE_YET, Session
from twisted.web.static import DirectoryLister

#Eh, this "should" work as nosetests puts its cwd in sys.path

from tx_sessions import Root


def test_if_registration_runs_without_error():
    request = TestRequest("",None)
    graph = Root()
    graph.on_register(request)


def test_if_registration_reports_error():
    request = TestRequest("",None)
    request.args['name'] = ['bob']

    request.session = Session({}, 123, )
    webuser = request.session.getComponent(IWebUser)
    webuser.name = "foo"

    graph = Root()

    payload = graph.on_register(request)
    assert isinstance(payload, basestring)
    msg = json.loads(payload)
    eq_(msg['success'], False, payload)
    eq_(msg['error'],  "Name already set to foo", payload)