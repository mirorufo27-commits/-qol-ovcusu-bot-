# conftest for pytest
import os
import tempfile

import pytest

@pytest.fixture
def tmp_db_path(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    return str(d)
