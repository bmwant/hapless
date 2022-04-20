from pathlib import Path

from hapless.utils import allow_missing


def read_file(path):
    with open(path) as f:
        return f.read()


def test_allow_missing_no_file():
    path = Path("does-not-exist")
    decorated = allow_missing(read_file)
    result = decorated(path)
    assert result is None


def test_allow_missing_file_exists():
    pass
