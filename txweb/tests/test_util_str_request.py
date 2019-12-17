import json
import io

from twisted.web.test import requesthelper
from twisted.python.compat import intToBytes
from txweb.lib.str_request import StrRequest

from pathlib import Path



def test_request_has_json_property():

    dummy = requesthelper.DummyChannel()

    r = StrRequest(dummy)
    expected = dict(number=123, word="foo", bool=True)
    r.requestHeaders.addRawHeader(b"Content-Type", b"application/json")
    r.content = io.BytesIO(json.dumps(expected).encode("utf-8"))
    r.json == expected

def test_request_processes_get_args():
    dummy = requesthelper.DummyChannel()
    r = StrRequest(dummy)
    r.content = io.BytesIO(b"")
    r.requestReceived(b"GET", b"/foo?hello=world&number=123", b"HTTP/1.1")

    assert "hello" in r.args
    assert "number" in r.args
    assert r.args["hello"][0] == "world"
    assert r.args["number"][0] == "123"

def test_request_processes_a_simple_form():

    test = b"word=test&checked=on&word=test2"

    dummy = requesthelper.DummyChannel()
    r = StrRequest(dummy)
    r.content = io.BytesIO(test)
    r.requestHeaders.setRawHeaders(b"Content-Type", [b"application/x-www-form-urlencoded"])
    r.requestHeaders.setRawHeaders(b"Content-Length", [b"31"])

    r.requestReceived(b"POST", b"/foo", b"HTTP/1.1")
    assert "word" in r.form
    assert r.form['word'] == "test"
    assert "checked" in r.form
    assert r.form["checked"] == "on"

def test_request_processes_a_multipart_form():

    test = \
b"""-----------------------------8693289853609
Content-Disposition: form-data; name="word"

test
-----------------------------8693289853609
Content-Disposition: form-data; name="a_file"; filename="LICENSE.txt"
Content-Type: text/plain

Copyright (C) 2011 by ominian.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
-----------------------------8693289853609--
"""

    dummy = requesthelper.DummyChannel()
    r = StrRequest(dummy)
    r.content = io.BytesIO(test)
    r.requestHeaders.setRawHeaders("Content-Type", [b"multipart/form-data; boundary=---------------------------8693289853609"])
    r.requestHeaders.setRawHeaders("Content-Length", [intToBytes(len(test))])

    r.requestReceived(b"POST", b"/foo", b"HTTP/1.1")
    assert "a_file" in r.files
    assert r.form["a_file"] is None
    r.files['a_file'].stream.read() == (Path(__file__).parent / "fixture" / "static" / "LICENSE.txt").read_bytes()