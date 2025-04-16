from pathlib import Path

import pytest


@pytest.fixture
def datadir():
    return Path(__file__).parent / "data"
