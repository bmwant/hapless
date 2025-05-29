import getpass
from pathlib import Path
from unittest.mock import MagicMock, patch

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
    assert isinstance(hap.name, str)
    assert hap.name.startswith("hap-")
    assert hap.pid is None
    assert hap.proc is None
    assert hap.rc is None
    assert hap.cmd == "false"
    assert hap.status == "failed"
    assert hap.env is None
    assert hap.restarts == 0
    assert not hap.active

    assert not hap.stdout_path.exists()
    assert not hap.stderr_path.exists()
    assert hap.start_time is None
    assert hap.end_time is None

    assert hap.runtime == "a moment"

    assert hap.accessible is True
    # Current user should be the owner of the hap
    assert hap.owner == getpass.getuser()


def test_hap_path_should_be_a_directory(tmp_path):
    hap_path = Path(tmp_path) / "hap-path"
    hap_path.touch()

    with pytest.raises(ValueError) as e:
        Hap(hap_path)

    assert f"Path {hap_path} is not a directory" == str(e.value)


def test_default_restarts(hap: Hap):
    assert hap.restarts == 0


def test_correct_restarts_value(tmp_path):
    hap = Hap(Path(tmp_path), name="hap-name@2", cmd="true")
    assert hap.restarts == 2


def test_raw_name(tmp_path):
    hap = Hap(Path(tmp_path), name="hap-name@3", cmd="true")
    assert hap.name == "hap-name"
    assert hap.raw_name == "hap-name@3"


def test_hap_inaccessible(hap: Hap):
    with patch("os.utime", side_effect=PermissionError):
        assert hap.accessible is False


def test_hap_owner_unknown_uid(hap: Hap):
    mocked_stat = MagicMock()
    mocked_stat.st_uid = 6249
    mocked_stat.st_gid = 6251

    with patch("pathlib.Path.stat", return_value=mocked_stat):
        assert hap.owner == "6249:6251"


def test_serialize(hap: Hap):
    serialized = hap.serialize()
    assert isinstance(serialized, dict)
    assert serialized["hid"] == hap.hid
    assert serialized["name"] == hap.name
    assert serialized["pid"] is None
    assert serialized["rc"] is None
    assert serialized["cmd"] == hap.cmd
    assert serialized["status"] == hap.status.value
    assert serialized["runtime"] == hap.runtime
    assert serialized["start_time"] is None
    assert serialized["end_time"] is None
    assert serialized["restarts"] == str(hap.restarts)
    assert serialized["stdout_file"] == str(hap.stdout_path)
    assert serialized["stderr_file"] == str(hap.stderr_path)
