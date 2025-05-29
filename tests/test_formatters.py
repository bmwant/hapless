from hapless.formatters import TableFormatter
from hapless.hap import Status


def test_table_formatter_status_text():
    formatter = TableFormatter()
    result = formatter._get_status_text(Status.SUCCESS)
    assert result.plain == "• success"
