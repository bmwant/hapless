from hapless.hap import Status


def test_get_status_text(hapless):
    result = hapless._get_status_text(Status.SUCCESS)
    assert result.plain == "• success"
