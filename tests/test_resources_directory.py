
from txweb.resources import Directory, SimpleFile
from txweb.web_views import WebSite

from pathlib import Path
import typing as T
from txweb.util.str_request import StrRequest
import pytest

from .helper import MockRequest

@pytest.fixture
def static_dir():
    return Path(__file__).parent / "fixture" / "static"


def test_sketch_out(static_dir):

    resource = Directory(static_dir, recurse=False)
    expected = {
        str(file.name):(file.stat().st_size,)
        for file in static_dir.glob("*")
        if file.exists() and file.is_file()
    }


    @resource.show_files
    def render_FILES(self, request: StrRequest, files: T.List[str]):
        buffer = {}
        for file in files:  # type: str
            file = Path(file)
            buffer[file.name] = (file.stat().st_size,)

        return buffer

    request = MockRequest([], "/")
    request.method = b"GET"
    actual = resource.render(request)
    assert actual == expected


def test_hybrid_leaf_and_branch(static_dir):

    request = MockRequest([], "/")
    request.method = b"GET"
    resource = Directory(static_dir)

    child = resource.getChild("", request)
    assert child == resource

    request = MockRequest([], "")
    request.method = b"GET"
    resource = Directory(static_dir)
    child = resource.getChild("LICENSE.txt", request) # type: SimpleFile


    assert child.path == str(static_dir / "LICENSE.txt")
    assert isinstance(child, SimpleFile)


def test_full_suite_with_routed_site_to_added_directory(static_dir):
    site = WebSite()

    site.add_directory("/some/convoluted_path", static_dir)

    request = MockRequest([], "/some/convoluted_path/LICENSE.txt")

    resource = site.getResourceFor(request)
    assert isinstance(resource, SimpleFile)

    


# TODO so many more tests needed
# I already know that getChild is going to break