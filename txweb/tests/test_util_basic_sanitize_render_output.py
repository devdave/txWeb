
import pytest

from txweb.util.basic import sanitize_render_output
from twisted.web.server import NOT_DONE_YET
from twisted.internet.defer import Deferred

def test_full_suite_coverage():

    assert sanitize_render_output("Foo") == b"Foo"
    assert sanitize_render_output(b"Foo") == b"Foo"

    with pytest.raises(RuntimeError):
        assert sanitize_render_output(("Foo",))

    assert sanitize_render_output(NOT_DONE_YET) == NOT_DONE_YET

    d = Deferred()

    assert sanitize_render_output(d) == NOT_DONE_YET

    assert sanitize_render_output(123) == b"123"