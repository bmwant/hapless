from pathlib import Path
from unittest.mock import ANY, Mock, patch

import pytest

from hapless.main import Hapless


def test_get_next_hap_id(hapless: Hapless):
    result = hapless._get_next_hap_id()
    assert result == "1"


def test_get_hap_dirs_empty(hapless: Hapless):
    result = hapless._get_hap_dirs()
    assert result == []


def test_get_hap_dirs_with_hap(hapless: Hapless, hap):
    result = hapless._get_hap_dirs()
    assert result == [hap.hid]


def test_create_hap(hapless: Hapless):
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


def test_get_hap_works_with_restarts(hapless: Hapless):
    raw_name = "hap-name@2"
    hapless.create_hap(cmd="true", name=raw_name)
    hap = hapless.get_hap(hap_alias="hap-name")
    assert hap is not None
    assert hap.raw_name == raw_name
    assert hap.name == "hap-name"

    # Check ignoring restarts suffix
    no_hap = hapless.get_hap(hap_alias=raw_name)
    assert no_hap is None


def test_rename_hap_preserves_restarts(hapless: Hapless):
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


def test_get_haps_only_accessible(hapless: Hapless):
    hap1 = hapless.create_hap("true", name="hap1")
    hap2 = hapless.create_hap("true", name="hap2")  # noqa: F841
    hap3 = hapless.create_hap("true", name="hap3")  # noqa: F841

    # NOTE: order is guaranteed, so we can rely on this side effect
    with patch(
        "os.access",
        side_effect=(True, False, False),
    ) as access_mock:
        haps = hapless.get_haps()
        assert access_mock.call_count == 3
        assert len(haps) == 1
        assert haps[0].name == hap1.name


def test_get_haps_return_all_entries(hapless: Hapless):
    hap1 = hapless.create_hap("true", name="hap1")
    hap2 = hapless.create_hap("true", name="hap2")  # noqa: F841
    hap3 = hapless.create_hap("true", name="hap3")  # noqa: F841

    with patch("os.access", return_value=False) as access_mock:
        haps = hapless.get_haps(accessible_only=False)
        # filter function just ignores accessible attribute
        access_mock.assert_not_called()
        assert len(haps) == 3
        assert hap1.accessible is False
        assert hap2.accessible is False
        assert hap3.accessible is False
        assert access_mock.call_count == 3


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


def test_run_hap_invocation(hapless: Hapless):
    """
    Check child launches a subprocess and exits.
    """
    hap = hapless.create_hap("echo test", name="hap-name")
    with patch("os.fork", return_value=0) as fork_mock, patch(
        "os.setsid"
    ) as setsid_mock, patch.object(
        hapless, "_wrap_subprocess"
    ) as wrap_subprocess_mock, patch.object(
        hapless, "_check_fast_failure"
    ) as check_fast_failure_mock:
        with pytest.raises(SystemExit) as e:
            hapless.run_hap(hap)
        assert e.value.code == 0

        fork_mock.assert_called_once_with()
        setsid_mock.assert_called_once_with()
        wrap_subprocess_mock.assert_called_once_with(hap)
        check_fast_failure_mock.assert_not_called()


def test_run_hap_parent_process(hapless: Hapless):
    """
    Check child launches a subprocess and exits.
    """
    hap = hapless.create_hap("echo test", name="hap-name")
    with patch("os.fork", return_value=12345) as fork_mock, patch.object(
        hapless, "_wrap_subprocess"
    ) as wrap_subprocess_mock, patch.object(
        hapless, "_check_fast_failure"
    ) as check_fast_failure_mock:
        hapless.run_hap(hap)

        fork_mock.assert_called_once()
        wrap_subprocess_mock.assert_not_called()
        check_fast_failure_mock.assert_not_called()


def test_run_hap_parent_process_blocking(hapless: Hapless):
    hap = hapless.create_hap("echo test", name="hap-blocking")
    with patch("os.fork") as fork_mock, patch.object(
        hapless, "_wrap_subprocess"
    ) as wrap_subprocess_mock, patch.object(
        hapless, "_check_fast_failure"
    ) as check_fast_failure_mock:
        hapless.run_hap(hap, blocking=True)

        # No forking, called directly in the parent process
        fork_mock.assert_not_called()
        check_fast_failure_mock.assert_not_called()
        wrap_subprocess_mock.assert_called_once_with(hap)


def test_run_hap_parent_process_with_check(hapless: Hapless):
    """
    Check parent process does not run a subprocess, but calls check.
    """
    hap = hapless.create_hap("echo test", name="hap-check")
    with patch("os.fork", return_value=12345) as fork_mock, patch.object(
        hapless, "_wrap_subprocess"
    ) as wrap_subprocess_mock, patch.object(
        hapless, "_check_fast_failure"
    ) as check_fast_failure_mock:
        hapless.run_hap(hap, check=True)

        fork_mock.assert_called_once()
        wrap_subprocess_mock.assert_not_called()
        check_fast_failure_mock.assert_called_once_with(hap)


def test_run_command_invocation(hapless: Hapless):
    with patch.object(hapless, "run_hap") as run_hap_mock:
        hapless.run_command("echo test")
        run_hap_mock.assert_called_once_with(ANY, check=False, blocking=False)


def test_run_command_accepts_redirect_stderr_parameter(hapless: Hapless):
    hap_mock = Mock()
    with patch.object(hapless, "run_hap") as run_hap_mock, patch.object(
        hapless, "create_hap", return_value=hap_mock
    ) as create_hap_mock:
        hapless.run_command("echo redirect", redirect_stderr=True)
        create_hap_mock.assert_called_once_with(
            cmd="echo redirect", hid=None, name=None, redirect_stderr=True
        )
        run_hap_mock.assert_called_once_with(hap_mock, check=False, blocking=False)


def test_redirect_stderr(hapless: Hapless):
    with patch("hapless.config.REDIRECT_STDERR", True):
        hap = hapless.create_hap(
            "python -c 'import sys; sys.stderr.write(\"redirected stderr\")'",
            name="hap-stderr",
        )
        assert hap.stderr_path == hap.stdout_path
        hapless.run_hap(hap, blocking=True)
        assert hap.stdout_path.exists()
        assert hap.stdout_path.read_text() == "redirected stderr"


def test_redirect_toggling_via_env_value(hapless: Hapless):
    with patch("hapless.config.REDIRECT_STDERR", True):
        hap1 = hapless.create_hap(
            cmd="python -c 'import sys; sys.stderr.write(\"redirected stderr1\")'",
            name="hap1-stderr",
        )
    with patch("hapless.config.REDIRECT_STDERR", False):
        hap2 = hapless.create_hap(
            cmd="python -c 'import sys; sys.stderr.write(\"not redirected stderr2\")'",
            name="hap2-stderr",
        )
    with patch("hapless.config.REDIRECT_STDERR", True):
        hap3 = hapless.create_hap(
            cmd="python -c 'import sys; sys.stderr.write(\"redirected stderr3\")'",
            name="hap3-stderr",
        )

    assert hap1.redirect_stderr is True
    assert hap2.redirect_stderr is False
    assert hap3.redirect_stderr is True

    # Run all three haps
    hapless.run_hap(hap1, blocking=True)
    hapless.run_hap(hap2, blocking=True)
    hapless.run_hap(hap3, blocking=True)

    assert hap1.stdout_path == hap1.stderr_path
    assert hap1.stdout_path.exists()
    assert hap1.stdout_path.read_text() == "redirected stderr1"

    assert hap2.stdout_path != hap2.stderr_path
    assert hap2.stdout_path.exists()
    assert hap2.stderr_path.exists()
    assert hap2.stdout_path.read_text() == ""
    assert hap2.stderr_path.read_text() == "not redirected stderr2"

    assert hap3.stdout_path == hap3.stderr_path
    assert hap3.stdout_path.exists()
    assert hap3.stdout_path.read_text() == "redirected stderr3"


def test_redirect_state_is_not_affected_after_creation(hapless: Hapless):
    hap = hapless.create_hap(
        cmd="python -c 'import sys; sys.stderr.write(\"redirected stderr\")'",
        name="hap-redirect",
        redirect_stderr=True,
    )

    with patch("hapless.config.REDIRECT_STDERR", False):
        hapless.run_hap(hap, blocking=True)

        assert hap.redirect_stderr is True
        assert hap.stdout_path == hap.stderr_path
        assert hap.stdout_path.exists()
        assert hap.stdout_path.read_text() == "redirected stderr"


@pytest.mark.parametrize("redirect_stderr", [True, False])
def test_restart_preservers_redirect_state(hapless: Hapless, redirect_stderr: bool):
    hap = hapless.create_hap(
        cmd="doesnotexist",
        name="hap-redirect-state",
        redirect_stderr=redirect_stderr,
    )
    hid = hap.hid
    assert hap.redirect_stderr is redirect_stderr

    with patch.object(hapless, "kill") as kill_mock, patch.object(
        hapless, "get_hap", return_value=hap
    ) as get_hap_mock, patch(
        "hapless.main.wait_created",
        return_value=True,
    ) as wait_created_mock, patch.object(hapless, "run_command") as run_command_mock:
        hapless.restart(hap)

        kill_mock.assert_not_called()
        get_hap_mock.assert_called_once_with(hid)
        wait_created_mock.assert_called_once_with(ANY, timeout=1)
        run_command_mock.assert_called_once_with(
            cmd="doesnotexist",
            hid=hid,
            name="hap-redirect-state@1",
            redirect_stderr=redirect_stderr,
        )


def test_same_handle_can_be_closed_twice(tmpdir):
    filepath = Path(tmpdir) / "samehandle.log"
    filepath.touch()
    stdout_handle = filepath.open("w")
    stderr_handle = stdout_handle
    stdout_handle.close()
    stderr_handle.close()
    assert stdout_handle.closed
    assert stderr_handle.closed


def test_spawn_is_used_instead_of_fork(hapless: Hapless):
    hap = hapless.create_hap("echo spawn1", name="hap-spawn-1")
    with patch("hapless.config.NO_FORK", True), patch.object(
        hapless, "_wrap_subprocess"
    ) as wrap_subprocess_mock, patch.object(
        hapless, "_run_via_fork"
    ) as run_fork_mock, patch.object(
        hapless, "_run_via_spawn"
    ) as run_spawn_mock, patch.object(
        hapless, "_check_fast_failure"
    ) as check_fast_failure_mock:
        hapless.run_hap(hap)

        run_spawn_mock.assert_called_once_with(hap)
        wrap_subprocess_mock.assert_not_called()
        run_fork_mock.assert_not_called()
        check_fast_failure_mock.assert_not_called()


def test_wrap_subprocess(hapless: Hapless):
    hap = hapless.create_hap(cmd="echo subprocess", name="hap-subprocess")
    with patch("subprocess.Popen") as popen_mock, patch.object(
        hap, "bind"
    ) as bind_mock, patch.object(hap, "set_return_code") as set_return_code_mock:
        popen_mock.return_value.pid = 12345
        popen_mock.return_value.wait.return_value = 0
        hapless._wrap_subprocess(hap)

        bind_mock.assert_called_once_with(12345)
        popen_mock.assert_called_once_with(
            "echo subprocess",
            shell=True,
            executable=ANY,
            stdout=ANY,
            stderr=ANY,
        )
        set_return_code_mock.assert_called_once_with(0)
