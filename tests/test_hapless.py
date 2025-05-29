from pathlib import Path
from unittest.mock import patch

import pytest

from hapless.main import Hapless


def test_get_next_hap_id(hapless):
    result = hapless._get_next_hap_id()
    assert result == "1"


def test_get_hap_dirs_empty(hapless):
    result = hapless._get_hap_dirs()
    assert result == []


def test_get_hap_dirs_with_hap(hapless, hap):
    result = hapless._get_hap_dirs()
    assert result == [hap.hid]


def test_create_hap(hapless):
    result = hapless.create_hap("echo hello")
    assert result.cmd == "echo hello"
    assert result.hid == "1"
    assert result.name is not None
    assert isinstance(result.name, str)
    assert result.name.startswith("hap-")


def test_create_hap_custom_hid(hapless: Hapless):
    result = hapless.create_hap(cmd="echo hello", hid="42", name="hap-name")
    assert result.cmd == "echo hello"
    assert result.hid == "42"
    assert result.name == "hap-name"


def test_get_hap_works_with_restarts(hapless):
    raw_name = "hap-name@2"
    hapless.create_hap(cmd="true", name=raw_name)
    hap = hapless.get_hap(hap_alias="hap-name")
    assert hap is not None
    assert hap.raw_name == raw_name
    assert hap.name == "hap-name"

    # Check ignoring restarts suffix
    no_hap = hapless.get_hap(hap_alias=raw_name)
    assert no_hap is None


def test_rename_hap_preserves_restarts(hapless):
    raw_name = "hap-name@3"
    hapless.create_hap(cmd="true", name=raw_name)
    hap = hapless.get_hap(hap_alias="hap-name")
    assert hap is not None
    assert hap.raw_name == raw_name
    assert hap.name == "hap-name"

    hapless.rename_hap(hap, "hap-new-name")
    no_hap = hapless.get_hap(hap_alias="hap-name")
    # Cannot get with with an old name
    assert no_hap is None

    hap = hapless.get_hap(hap_alias="hap-new-name")
    assert hap is not None
    assert hap.restarts == 3
    assert hap.name == "hap-new-name"
    assert hap.raw_name == "hap-new-name@3"


def test_get_haps_only_accessible(hapless):
    hap1 = hapless.create_hap("true", name="hap1")
    hap2 = hapless.create_hap("true", name="hap2")  # noqa: F841
    hap3 = hapless.create_hap("true", name="hap3")  # noqa: F841

    # NOTE: order is guaranteed, so we can rely on this side effect
    with patch("os.utime", side_effect=(None, PermissionError, PermissionError)):
        haps = hapless.get_haps()
        assert len(haps) == 1
        assert haps[0].name == hap1.name


def test_get_haps_return_all_entries(hapless):
    hap1 = hapless.create_hap("true", name="hap1")
    hap2 = hapless.create_hap("true", name="hap2")  # noqa: F841
    hap3 = hapless.create_hap("true", name="hap3")  # noqa: F841

    with patch("os.utime", side_effect=PermissionError):
        haps = hapless.get_haps(accessible_only=False)
        assert len(haps) == 3
        assert hap1.accessible is False
        assert hap2.accessible is False
        assert hap3.accessible is False


def test_state_dir_is_not_accessible(tmpdir, capsys):
    with patch("os.utime", side_effect=PermissionError):
        with pytest.raises(SystemExit) as e:
            Hapless(hapless_dir=Path(tmpdir))

        captured = capsys.readouterr()

        assert "is not accessible by user" in captured.out
        assert e.value.code == 1


def test_state_dir_is_overriden(tmpdir):
    custom_state_dir = f"{tmpdir}/custom"
    hapless = Hapless(hapless_dir=custom_state_dir)

    assert isinstance(hapless.dir, Path)
    assert str(hapless.dir) == custom_state_dir

    hap = hapless.create_hap(cmd="echo hello", hid="42", name="hap-name")
    assert hap.path.parent == Path(custom_state_dir)
    assert hap.path == Path(custom_state_dir) / hap.hid
