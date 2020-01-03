
import pytest
from .helper import RequestRetval, requesthelper
from .helper import StrRequest

from io import BytesIO

@pytest.fixture(scope="function")
def dummy_request() -> RequestRetval:
    channel = requesthelper.DummyChannel()
    request = StrRequest(channel)
    request.channel = channel
    request.content = BytesIO()

    return RequestRetval(request, channel)