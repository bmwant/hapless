from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from hapless.hap import Hap, Status
from hapless.main import Hapless


def all_equal(iterable):
    return len(set(iterable)) <= 1


def test_random_name_generation():
    name_length = 8
    name_count = 4
    names = []
    for _ in range(name_count):
        new_name = Hap.get_random_name(length=name_length)
        assert len(new_name) == name_length
        names.append(new_name)

    assert not all_equal(names)


def test_unbound_hap(hap: Hap):
    assert isinstance(hap.name, str)
    assert hap.name.startswith("hap-")
    assert hap.pid is None
    assert hap.proc is None
    assert hap.rc is None
    assert hap.cmd == "false"
    assert hap.status == Status.UNBOUND
    assert hap.env is None
    assert hap.restarts == 0
    assert not hap.active
