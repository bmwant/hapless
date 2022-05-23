from pathlib import Path
from unittest.mock import Mock

import click
import pytest

from hapless.utils import allow_missing, validate_signal


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


def test_validate_signal_wrong_code():
    ctx = click.get_current_context(silent=True)
    param = Mock()
    with pytest.raises(click.BadParameter) as excinfo:
        validate_signal(ctx, param, "not-a-number")

    assert str(excinfo.value) == "Signal should be a valid integer value"


def test_validate_signal_out_of_bounds():
    pass
