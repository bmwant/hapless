import json

from hapless.formatters import JSONFormatter, TableFormatter
from hapless.hap import Hap, Status
from hapless.main import Hapless


def test_table_formatter_status_text():
    formatter = TableFormatter()
    result = formatter._get_status_text(Status.SUCCESS)
    assert result.plain == "• success"


def test_json_formatter_single_hap(hap: Hap):
    formatter = JSONFormatter()
    result = formatter.format_one(hap)
    assert isinstance(result, str)
    assert result[0] == "{"
    assert hap.name in result
    assert '"pid": null' in result
    assert result[-1] == "}"
    # Check if it is a valid JSON
    obj = json.loads(result)
    assert isinstance(obj, dict)
    assert "name" in obj
    assert obj["name"] == hap.name


def test_json_formatter_multiple_haps(hapless: Hapless):
    haps = [
        hapless.create_hap("true", name="hap1"),
        hapless.create_hap("true", name="hap2"),
        hapless.create_hap("true", name="hap3"),
    ]

    formatter = JSONFormatter()
    result = formatter.format_list(haps)
    assert isinstance(result, str)
    assert result[0] == "["
    assert "hap1" in result
    assert "hap2" in result
    assert "hap3" in result
    assert "null" in result
    assert "{" in result
    assert "}" in result
    assert result[-1] == "]"
    # Check if it is a valid JSON
    objects = json.loads(result)
    assert isinstance(objects, list)
    assert len(objects) == len(haps)
