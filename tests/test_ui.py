from hapless.formatters import TableFormatter
from hapless.ui import ConsoleUI


def test_default_formatter_is_table():
    ui = ConsoleUI()
    assert isinstance(ui.default_formatter, TableFormatter)
