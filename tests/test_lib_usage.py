from pathlib import Path

import pytest

from hapless import Hap, Hapless, Status, config


def test_creation(tmpdir):
    hapless = Hapless(hapless_dir=Path(tmpdir))
    hap1 = hapless.create_hap("echo one", name="hap-one")
    hap2 = hapless.create_hap("echo two", name="hap-two")

    assert isinstance(hap1, Hap)
    assert isinstance(hap2, Hap)
    assert hap1.hid != hap2.hid
    assert hap1.name == "hap-one"
    assert hap2.name == "hap-two"

    assert hap1.status == Status.UNBOUND


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


def test_can_set_redirection_via_config(hapless: Hapless):
    """
    Test that redirection can be set programmatically when using Hapless interface.
    """
    config.REDIRECT_STDERR = True
    hap = hapless.create_hap(
        cmd="python -c 'import sys; sys.stderr.write(\"redirected stderr\")'",
        name="hap-stderr",
    )

    assert hap.stderr_path == hap.stdout_path
    hapless.run_hap(hap, blocking=True)
    assert hap.stdout_path.exists()
    assert hap.stdout_path.read_text() == "redirected stderr"

    hap_reread = hapless.get_hap(hap.hid)
    assert hap_reread is not None
    assert hap_reread.stderr_path == hap_reread.stdout_path
    assert not hap_reread._stderr_path.exists()
