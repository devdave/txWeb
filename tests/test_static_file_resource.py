
from txweb.web_views import WebSite

from twisted.web.server import NOT_DONE_YET
from twisted.web.static import File
from twisted.web.resource import getChildForRequest

from .helper import MockRequest

from pathlib import Path


"""
Reference tests for how I can hack around File.

One complication is that File resource has isLeaf set to 0/False so it's not meant to
be rendered directly but instead through getChild
"""
def test_serves_a_file():

    license = Path(__file__).parent / "fixture" / "static" / "LICENSE.txt" # type: Path

    resource = File(str(license))

    request = MockRequest(["LICENSE.txt"], "/LICENSE.txt")

    response = resource.render(request)
    actual = license.read_bytes()


    assert response == NOT_DONE_YET
    assert len(request.written) == 1
    expected = request.written[0]
    assert len(actual) == len(expected)


def test_serves_a_directory():
    license = Path(__file__).parent / "fixture" / "static" / "LICENSE.txt"  # type: Path

    request = MockRequest(["irrelevant","past","path"], "license.txt")

    file_resource = File(str(license.parent))
    dir_resource = file_resource.getChild("license.txt", request)


    response = dir_resource.render(request)

    actual = license.read_bytes()
    assert response == NOT_DONE_YET
    assert len(request.written) == 1
    expected = request.written[0]
    assert len(actual) == len(expected)

