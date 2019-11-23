
from .helper import MockRequest

from txweb.resources.simple_file import SimpleFile
from pathlib import Path

from twisted.web.server import NOT_DONE_YET



def test_instantiates():

    file_path = Path(__file__).parent / "fixture" / "static" / "LICENSE.txt" # type: Path
    assert file_path.exists()

    request = MockRequest([], "/foo")
    resource = SimpleFile(file_path, defaultType="text/plain")
    response = resource.render_GET(request)
    assert response == NOT_DONE_YET
    assert len(request.written) == 1 #  Expect only one thing to have been written here
    assert request.written[0] == file_path.read_bytes()


def test_supports_single_ranged_writes():
    file_path = Path(__file__).parent / "fixture" / "static" / "LICENSE.txt"  # type: Path
    assert file_path.exists()

    request = MockRequest([], "/foo")
    resource = SimpleFile(file_path, defaultType="text/plain")
    request.requestHeaders.setRawHeaders(b"range", [b"bytes=100-200"])

    response = resource.render_GET(request)
    assert response == NOT_DONE_YET
    assert len(request.written) == 1
    expected = file_path.read_bytes()
    expected = expected[100:201]
    actual = request.written[0]

    assert len(actual) == len(expected)
    assert actual == expected

