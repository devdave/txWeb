
from .helper import MockRequest

from txweb.resources.simple_file import SimpleFile
from pathlib import Path

from twisted.web.server import NOT_DONE_YET

import pytest

@pytest.fixture
def license():
    file_path = Path(__file__).parent / "fixture" / "static" / "LICENSE.txt" #  type: Path
    assert file_path.exists()
    return file_path


def test_instantiates(license):


    request = MockRequest([], "/foo")
    resource = SimpleFile(license, defaultType="text/plain")
    response = resource.render_GET(request)
    assert response == NOT_DONE_YET
    assert len(request.written) == 1 #  Expect only one thing to have been written here
    assert request.written[0] == license.read_bytes()


def test_supports_single_ranged_read(license):


    request = MockRequest([], "/foo")
    resource = SimpleFile(license, defaultType="text/plain")
    request.requestHeaders.setRawHeaders(b"range", [b"bytes=100-200"])

    response = resource.render_GET(request)
    assert response == NOT_DONE_YET
    assert len(request.written) == 1
    expected = license.read_bytes()
    expected = expected[100:201]
    actual = request.written[0]

    assert len(actual) == len(expected)
    assert actual == expected


def test_multiple_ranges(license):


    request = MockRequest([], "/foo")
    resource = SimpleFile(license, defaultType="text/plain")

    request.requestHeaders.setRawHeaders(b"range", [b"bytes=0-499, -500"])

    assert resource.render(request) == NOT_DONE_YET
    assert len(request.written) == 1

    raw_file = license.read_bytes()

    content_type = request.responseHeaders.getRawHeaders("content-type")[0]
    ct_type, ct_boundary = content_type.split(";")
    _, dividier =ct_boundary.split("=")
    dividier = dividier.strip().strip("\"")

    parts = request.written[0].decode("utf-8").split(dividier)

    assert len(parts) == 4

    expected1 = raw_file[0:500]
    expected2 = raw_file[-501]



