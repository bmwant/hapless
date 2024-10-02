from hapless.hap import Status
from hapless.ui import ConsoleUI


def test_get_status_text():
    ui = ConsoleUI()
    result = ui._get_status_text(Status.SUCCESS)
    assert result.plain == "• success"
