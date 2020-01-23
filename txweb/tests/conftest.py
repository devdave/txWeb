
from pathlib import Path

import pytest
from .helper import RequestRetval, requesthelper
from .helper import StrRequest

from io import BytesIO

@pytest.fixture(scope="session")
def static_dir():
    return Path(__file__).parent / "fixture" / "static"

@pytest.fixture(scope="function")
def dummy_request() -> RequestRetval:
    channel = requesthelper.DummyChannel()
    request = StrRequest(channel)
    request.channel = channel
    request.content = BytesIO()

    return RequestRetval(request, channel)