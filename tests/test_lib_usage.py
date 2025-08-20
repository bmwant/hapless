import operator
from pathlib import Path

import pytest

from hapless import Hap, Hapless, Status


def test_creation(tmp_path):
    hapless = Hapless(hapless_dir=tmp_path)
    hap1 = hapless.create_hap("echo one", name="hap-one")
    hap2 = hapless.create_hap("echo two", name="hap-two")

    assert isinstance(hap1, Hap)
    assert isinstance(hap2, Hap)
    assert hap1.hid != hap2.hid
    assert hap1.name == "hap-one"
    assert hap2.name == "hap-two"

    assert hap1.status == Status.UNBOUND


def test_quiet_mode(tmp_path, capsys):
    """
    Check that quiet mode suppresses output.
    """
    hapless = Hapless(hapless_dir=tmp_path, quiet=True)
    hap = hapless.create_hap("false")
    with pytest.raises(SystemExit) as e:
        hapless.pause_hap(hap)

    captured = capsys.readouterr()
    assert e.value.code == 1
    assert captured.out == ""
    assert captured.err == ""


def test_can_set_redirection_on_create(hapless: Hapless):
    """
    Test that redirection can be set programmatically when using Hapless interface.
    """
    hap = hapless.create_hap(
        cmd="python -c 'import sys; sys.stderr.write(\"redirected stderr\")'",
        name="hap-stderr",
        redirect_stderr=True,
    )

    assert hap.stderr_path == hap.stdout_path
    hapless.run_hap(hap, blocking=True)
    assert hap.stdout_path.exists()
    assert hap.stdout_path.read_text() == "redirected stderr"

    # Redirect state should be preserved between re-reads
    hap_reread = hapless.get_hap(hap.hid)
    assert hap_reread is not None
    assert hap_reread.stderr_path == hap_reread.stdout_path
    assert not hap_reread._stderr_path.exists()


def test_toggling_redirect_state(hapless: Hapless):
    hap1 = hapless.create_hap(
        cmd="python -c 'import sys; sys.stderr.write(\"redirected stderr1\")'",
        name="hap1-stderr",
        redirect_stderr=True,
    )
    hap2 = hapless.create_hap(
        cmd="python -c 'import sys; sys.stderr.write(\"not redirected stderr2\")'",
        name="hap2-stderr",
        redirect_stderr=False,
    )
    hap3 = hapless.create_hap(
        cmd="python -c 'import sys; sys.stderr.write(\"redirected stderr3\")'",
        name="hap3-stderr",
        redirect_stderr=True,
    )

    assert hap1.redirect_stderr is True
    assert hap2.redirect_stderr is False
    assert hap3.redirect_stderr is True

    # Run all three haps
    hapless.run_hap(hap1, blocking=True)
    hapless.run_hap(hap2, blocking=True)
    hapless.run_hap(hap3, blocking=True)

    assert hap1.stdout_path.exists()
    assert hap1.stdout_path.read_text() == "redirected stderr1"

    assert hap2.stdout_path.exists()
    assert hap2.stderr_path.exists()
    assert hap2.stdout_path.read_text() == ""
    assert hap2.stderr_path.read_text() == "not redirected stderr2"

    assert hap3.stdout_path.exists()
    assert hap3.stdout_path.read_text() == "redirected stderr3"

    # Check redirect state is the same after re-reading
    haps = hapless.get_haps()
    redirects = list(map(operator.attrgetter("redirect_stderr"), haps))
    assert redirects == [True, False, True]
