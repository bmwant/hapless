from pathlib import Path

import pytest

from hapless.hap import Hap


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
    assert hap.pid is None
    assert hap.proc is None
    assert hap.rc is None
    assert hap.cmd == "false"
    assert hap.status == "failed"
    assert hap.env is None
    assert not hap.active

    assert not hap.stdout_path.exists()
    assert not hap.stderr_path.exists()
    assert hap.start_time is None
    assert hap.end_time is None

    assert hap.runtime == "a moment"


def test_hap_path_should_be_a_directory(tmp_path):
    hap_path = Path(tmp_path) / "hap-path"
    hap_path.touch()

    with pytest.raises(ValueError) as e:
        Hap(hap_path)

    assert f"Path {hap_path} is not a directory" == str(e.value)
