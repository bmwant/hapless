from pathlib import Path
from typing import Generator
from unittest.mock import ANY, PropertyMock, patch

import pytest

from hapless.formatters import TableFormatter
from hapless.main import Hapless
from hapless.ui import ConsoleUI


@pytest.fixture
def hapless_with_ui(tmp_path: Path) -> Generator[Hapless, None, None]:
    hapless = Hapless(hapless_dir=tmp_path, quiet=False)
    # Set a fixed width for the console to be able to assert on content that could fit
    hapless.ui.console.width = 180
    yield hapless


def test_default_formatter_is_table():
    ui = ConsoleUI()
    assert isinstance(ui.default_formatter, TableFormatter)


def test_long_hids_are_visible(capsys, hapless: Hapless):
    ui = ConsoleUI()
    long_hid = "9876543210"
    hap = hapless.create_hap("true", hid=long_hid)
    ui.stats([hap])
    captured = capsys.readouterr()
    assert long_hid in captured.out
    assert hap.name in captured.out


def test_summary_and_details_disabled_in_quiet_mode(capsys, hapless: Hapless):
    hap = hapless.create_hap("true")

    hapless.show(hap, formatter=TableFormatter())
    captured = capsys.readouterr()
    assert not captured.out
    assert not captured.err

    hapless.stats([hap], formatter=TableFormatter())
    captured = capsys.readouterr()
    assert not captured.out
    assert not captured.err


def test_disabled(capsys):
    ui = ConsoleUI(disable=True)
    ui.print("This should not be printed")
    ui.error("This should not be printed either")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_pause_message(hapless_with_ui: Hapless, capsys):
    hapless = hapless_with_ui
    hap = hapless.create_hap("true")
    with patch.object(hap, "proc") as proc_mock:
        hapless.pause_hap(hap)

        proc_mock.suspend.assert_called_once_with()
        captured = capsys.readouterr()
        assert "Paused" in captured.out

    with patch("sys.exit") as exit_mock, patch.object(hap, "proc", new=None):
        hapless.pause_hap(hap)

        exit_mock.assert_called_once_with(1)
        captured = capsys.readouterr()
        assert "Cannot pause" in captured.out
        assert "is not running" in captured.out


def test_resume_message(hapless_with_ui: Hapless, capsys):
    hapless = hapless_with_ui
    hap = hapless.create_hap("true")
    with patch.object(hap, "proc") as proc_mock:
        proc_mock.status.return_value = "stopped"
        hapless.resume_hap(hap)

        proc_mock.resume.assert_called_once_with()
        captured = capsys.readouterr()
        assert "Resumed" in captured.out

    with patch("sys.exit") as exit_mock, patch.object(hap, "proc", new=None):
        hapless.resume_hap(hap)

        exit_mock.assert_called_once_with(1)
        captured = capsys.readouterr()
        assert "Cannot resume" in captured.out
        assert "is not suspended" in captured.out


def test_rename_message(hapless_with_ui: Hapless, capsys):
    hapless = hapless_with_ui
    hap = hapless.create_hap("true", name="old-name")
    hapless.rename_hap(hap, new_name="new-name")

    captured = capsys.readouterr()
    assert "Renamed" in captured.out
    assert "old-name" in captured.out
    assert "new-name" in captured.out


def test_workdir_is_displayed_in_verbose_mode(
    hapless_with_ui: Hapless, tmp_path, capsys
):
    hapless = hapless_with_ui
    hap = hapless.create_hap("true", workdir=tmp_path)
    hapless.show(hap, formatter=TableFormatter(verbose=True))

    captured = capsys.readouterr()
    assert "Command:" in captured.out
    assert "Working dir:" in captured.out
    assert f"{tmp_path}" in captured.out


def test_launching_message(hapless_with_ui: Hapless, capsys):
    hapless = hapless_with_ui
    hap = hapless.create_hap("true")

    with patch.object(
        hapless, "_wrap_subprocess"
    ) as wrap_subprocess_mock, patch.object(
        hapless, "_run_via_spawn"
    ) as run_spawn_mock, patch.object(
        hapless, "_run_via_fork"
    ) as run_fork_mock, patch.object(
        hapless, "_check_fast_failure"
    ) as check_fast_failure_mock:
        hapless.run_hap(hap)

        wrap_subprocess_mock.assert_not_called()
        run_spawn_mock.assert_not_called()
        run_fork_mock.assert_called_once_with(hap)
        check_fast_failure_mock.assert_not_called()

    captured = capsys.readouterr()
    assert "Launching hap" in captured.out


def test_check_fast_failure_ok_message(hapless_with_ui: Hapless, capsys):
    hapless = hapless_with_ui
    hap = hapless.create_hap("echo check", name="hap-check-message")
    with patch.object(
        hapless, "_wrap_subprocess"
    ) as wrap_subprocess_mock, patch.object(
        hapless, "_run_via_spawn"
    ) as run_spawn_mock, patch.object(
        hapless, "_run_via_fork"
    ) as run_fork_mock, patch.object(
        hapless, "_check_fast_failure", wraps=hapless._check_fast_failure
    ) as check_fast_failure_mock, patch(
        "hapless.main.wait_created", return_value=False
    ) as wait_created_mock:
        hapless.run_hap(hap, check=True)

        wrap_subprocess_mock.assert_not_called()
        run_spawn_mock.assert_not_called()
        run_fork_mock.assert_called_once_with(hap)
        check_fast_failure_mock.assert_called_once_with(hap)
        wait_created_mock.assert_called_once()

    captured = capsys.readouterr()
    assert "Launching hap" in captured.out
    assert "hap-check-message" in captured.out
    assert "Hap is healthy and still running" in captured.out


def test_check_fast_failure_error_message(hapless_with_ui: Hapless, capsys):
    hapless = hapless_with_ui
    hap = hapless.create_hap("false", name="hap-check-failed-msg")
    with patch.object(type(hap), "rc", new_callable=PropertyMock) as rc_mock, patch(
        "hapless.main.wait_created", return_value=True
    ) as wait_created_mock:
        rc_mock.return_value = 1

        with pytest.raises(SystemExit) as e:
            hapless._check_fast_failure(hap)
        assert e.value.code == 1

        assert hap.rc == 1
        wait_created_mock.assert_called_once_with(
            hap._rc_file,
            live_context=ANY,
            interval=ANY,
            timeout=ANY,
        )

    captured = capsys.readouterr()
    assert "Hap exited too quickly" in captured.out
    assert "Hap is healthy" not in captured.out


def test_check_fast_failure_quick_but_success(hapless_with_ui: Hapless, capsys):
    hapless = hapless_with_ui
    hap = hapless.create_hap("true", name="hap-check-fast-ok")
    with patch.object(
        type(hap), "rc", new_callable=PropertyMock, return_value=0
    ), patch("hapless.main.wait_created", return_value=True) as wait_created_mock:
        hapless._check_fast_failure(hap)

        assert hap.rc == 0
        wait_created_mock.assert_called_once_with(
            hap._rc_file,
            live_context=ANY,
            interval=ANY,
            timeout=ANY,
        )

    captured = capsys.readouterr()
    assert "Hap exited too quickly" in captured.out
    assert "Hap is healthy" not in captured.out
