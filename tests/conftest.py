import shutil
from pathlib import Path
from tempfile import mkdtemp

import pytest
from ape import config

DATA_FOLDER = Path(mkdtemp()).resolve()
config.DATA_FOLDER = DATA_FOLDER


@pytest.fixture(scope="session", autouse=True)
def clean_datafolder():
    yield  # Run all collected tests.
    shutil.rmtree(DATA_FOLDER, ignore_errors=True)
