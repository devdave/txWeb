

import unittest
import typing as T
from unittest.mock import MagicMock
from dataclasses import dataclass
from io import BytesIO


import pytest

from txweb.lib.str_request import StrRequest
from txweb import Application

from twisted.web.test.test_web import DummyRequest
from twisted.web.test import requesthelper

class Helper(unittest.TestCase):
    def runTest(self):
        pass

helper = Helper()


@dataclass
class RequestRetval(object):
    request: StrRequest
    channel: requesthelper.DummyChannel

    @property
    def site(self):
        return self.request.site

    @site.setter
    def site(self, value):
        self.request.site = value
        self.channel.site = value


    def setup(self, app:Application):
        self.site = app.site
        self.request.channel = self.channel
        self.request.content = BytesIO()

    def read(self):
        self.channel.transport.written.seek(0,0)
        return self.channel.transport.written.read()

    def response_contains(self, search: str):
        return search in self.read()







ensureBytes = lambda x: x if isinstance(x, bytes) else x.encode()


class MockRequest(DummyRequest):# prama: no cover
    """
        Utility class that builds on DummyRequest to fullfill some missing methods
    """
    def __init__(self, postpath = [], path = "/", args = {}):
        DummyRequest.__init__(self, postpath)
        self.path = ensureBytes(path)
        self.postpath = self.path.split(b"/")
        self.prepath = []

        self.redirectToURL = None
        for name, arg in args.items():
            self.addArg(name, arg)


    def redirect(self, url):
        """
            Just a simple trap to catch if .redirect was called and what the URL is
        """
        self.redirectToURL = url

    def isSecure(self):
        return False

    def getHeader(self, name):

        if isinstance(name, str):
            name = name.encode("utf-8")

        return super().getHeader(name)
