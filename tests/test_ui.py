from hapless.formatters import TableFormatter
from hapless.ui import ConsoleUI


def test_default_formatter_is_table():
    ui = ConsoleUI()
    assert isinstance(ui.default_formatter, TableFormatter)


def test_long_hids_are_visible(capsys, hapless):
    ui = ConsoleUI()
    long_hid = "9876543210"
    hap = hapless.create_hap("true", hid=long_hid)
    ui.stats([hap])
    captured = capsys.readouterr()
    assert long_hid in captured.out
    assert hap.name in captured.out


def test_disabled(capsys):
    ui = ConsoleUI(disable=True)
    ui.print("This should not be printed")
    ui.error("This should not be printed either")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
