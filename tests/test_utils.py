import os
import signal
from pathlib import Path
from unittest.mock import Mock

import click
import pytest

from hapless.utils import allow_missing, kill_proc_tree, validate_signal


def read_file(path):
    with open(path) as f:
        return f.read()


def test_allow_missing_no_file():
    path = Path("does-not-exist")
    decorated = allow_missing(read_file)
    result = decorated(path)
    assert result is None


def test_allow_missing_file_exists(tmp_path):
    path = tmp_path / "file.txt"
    path.write_text("content")
    decorated = allow_missing(read_file)
    result = decorated(path)
    assert result == "content"


def test_validate_signal_wrong_code():
    ctx = click.get_current_context(silent=True)
    param = Mock()
    with pytest.raises(click.BadParameter) as excinfo:
        validate_signal(ctx, param, "not-a-number")

    assert str(excinfo.value) == "Signal should be a valid integer value"


def test_validate_signal_out_of_bounds():
    ctx = click.get_current_context(silent=True)
    param = Mock()
    code = signal.NSIG
    with pytest.raises(click.BadParameter) as excinfo:
        validate_signal(ctx, param, code)

    assert str(excinfo.value) == f"{code} is not a valid signal code"


def test_kill_proc_tree_fails_with_current_pid():
    pid = os.getpid()
    with pytest.raises(ValueError) as excinfo:
        kill_proc_tree(pid)

    assert str(excinfo.value) == "Would not kill myself"
