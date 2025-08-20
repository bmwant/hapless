import getpass
import json
import os
import re
from io import StringIO
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

    assert hap.stdout_path.exists()
    # NOTE: this file behaves as a flag, if it exists we do not want to redirect stderr
    assert hap.stderr_path.exists()
    assert hap.start_time is None
    assert hap.end_time is None

    assert hap.runtime == "a moment"

    assert hap.accessible is True
    # Current user should be the owner of the hap
    assert hap.owner == getpass.getuser()
    assert isinstance(hap.workdir, Path)
    assert str(hap.workdir) == os.getcwd()


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


@pytest.mark.parametrize("redirect_stderr", [True, False])
def test_correct_redirect_state(tmp_path, log_output, redirect_stderr):
    hap = Hap(
        Path(tmp_path),
        name="hap-name",
        cmd="doesnotexist",
        redirect_stderr=redirect_stderr,
    )

    assert hap.redirect_stderr is redirect_stderr
    assert ("stderr will be redirected to stdout" in log_output.text) is redirect_stderr


def test_hap_inaccessible(hap: Hap):
    with patch("os.access", return_value=False) as access_mock:
        assert hap.accessible is False
        access_mock.assert_called_once_with(
            hap.path, os.F_OK | os.R_OK | os.W_OK | os.X_OK
        )


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
    # check all the fields are json-serializable
    result = json.dumps(serialized)
    assert isinstance(result, str)
    assert "workdir" in result


def test_represent_unbound_hap(hapless: Hapless, capsys):
    hap = hapless.create_hap("echo print", name="hap-print")
    assert f"{hap}" == "#1 (hap-print)"
    # default is <hapless.hap.Hap object at 0x103960440>
    # <Hap #1 (hap-print) object at 0x102abc4e5>
    repr_pattern = r"<Hap #1 \(hap-print\) object at 0x[0-9a-f]+>"
    assert re.match(repr_pattern, repr(hap))

    # Test rich representation
    buffer = StringIO()
    test_console = Console(
        file=buffer,
        force_terminal=True,
        color_system="truecolor",
    )
    test_console.print(hap)
    result = buffer.getvalue().strip()
    assert (
        result
        == "hap ⚡️\x1b[1;36m1\x1b[0m \x1b[1m(\x1b[0m\x1b[1;38;2;253;202;64mhap-print\x1b[0m\x1b[1m)\x1b[0m"
    )
