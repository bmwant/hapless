from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest

from hapless.formatters import TableFormatter
from hapless.main import Hapless
from hapless.ui import ConsoleUI


@pytest.fixture
def hapless_with_ui(tmpdir) -> Generator[Hapless, None, None]:
    yield Hapless(hapless_dir=Path(tmpdir), quiet=False)


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
