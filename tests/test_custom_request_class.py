import json
import io

from twisted.web.test import requesthelper
from txweb.util.str_request import StrRequest



def test_request_has_json_property():

    dummy = requesthelper.DummyChannel()

    r = StrRequest(dummy)
    expected = dict(number=123, word="foo", bool=True)
    r.requestHeaders.addRawHeader("Content-Type", "application/json")
    r.content = io.BytesIO(json.dumps(expected).encode("utf-8"))
    r.json == expected
