from pathlib import Path

import pytest

from hapless import Hap, Hapless, Status


def test_creation(tmpdir):
    hapless = Hapless(hapless_dir=Path(tmpdir))
    hap1 = hapless.create_hap("echo one", name="hap-one")
    hap2 = hapless.create_hap("echo two", name="hap-two")

    assert isinstance(hap1, Hap)
    assert isinstance(hap2, Hap)
    assert hap1.hid != hap2.hid
    assert hap1.name == "hap-one"
    assert hap2.name == "hap-two"

    # TODO: fix this so it is unbound instead
    assert hap1.status == Status.FAILED


def test_quiet_mode(tmpdir, capsys):
    """
    Check that quiet mode suppresses output.
    """
    hapless = Hapless(hapless_dir=Path(tmpdir), quiet=True)
    hap = hapless.create_hap("false")
    with pytest.raises(SystemExit) as e:
        hapless.pause_hap(hap)

    captured = capsys.readouterr()
    assert e.value.code == 1
    assert captured.out == ""
    assert captured.err == ""
