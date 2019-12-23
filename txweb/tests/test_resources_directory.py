from txweb.resources import Directory, SimpleFile
from txweb import Application
from txweb.errors import HTTP404

from pathlib import Path
import typing as T
from txweb.lib.str_request import StrRequest
import pytest

from .helper import MockRequest


@pytest.fixture
def static_dir():
    return Path(__file__).parent / "fixture" / "static"


def test_sketch_out(static_dir):
    resource = Directory(static_dir, recurse=False)
    expected = {
        str(file.name): (file.stat().st_size,)
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
    request = MockRequest([], b"/")
    request.method = b"GET"
    resource = Directory(static_dir)

    child = resource.getChild(b"", request)
    assert child == resource

    request = MockRequest([], "")
    request.method = b"GET"
    resource = Directory(static_dir)
    child = resource.getChild(b"LICENSE.txt", request)  # type: SimpleFile

    assert child.path == str(static_dir / "LICENSE.txt")
    assert isinstance(child, SimpleFile)


def test_full_suite_with_routed_site_to_added_directory(static_dir):

    test_app = Application()
    test_app(__name__)


    test_app.add_staticdir("/some/convoluted_path", static_dir)

    request = MockRequest([], "/some/convoluted_path/LICENSE.txt")

    resource = test_app.site.getResourceFor(request)

    assert isinstance(resource, SimpleFile)


def test_full_suite_with_empty_url(static_dir):
    #  TODO relocate to static_dir/directory test suite
    test_app = Application(namespace=__name__)
    test_app.add_staticdir("/some/path", static_dir)

    request = MockRequest([], "/some/path/")

    resource = test_app.site.getResourceFor(request)
    assert isinstance(resource, Directory)


def test_full_suite_with_bad_url(static_dir):
    test_app = Application(namespace=__name__)

    test_app.add_staticdir("/some/path", static_dir)

    request = MockRequest([], "/some/path/FOO.bar")

    assert test_app.site._lastError is None
    with pytest.raises(HTTP404):
        resource = test_app.site.getResourceFor(request)


def test_simple_security_check_ensure_allowedfiles_is_limited(static_dir):
    resource = Directory(static_dir)
    assert len(resource.allowedFiles()) == 2


def test_render_Get_is_called_correctly(static_dir):
    import json

    directory = Directory(static_dir)
    request = MockRequest([], "/")
    with pytest.raises(NotImplementedError):
        response = directory.render(request)

    @directory.handleGet
    def render(parent, request, allowedFiles):
        response = {}
        response['count'] = len(allowedFiles)
        response['names'] = [x.name for x in allowedFiles]
        return json.dumps(response)

    response = directory.render(request)

# TODO so many more tests needed
# I already know that getChild is going to break
