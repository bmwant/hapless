from unittest.mock import Mock, PropertyMock, patch

import pytest

from hapless.cli_utils import get_or_exit


@patch("hapless.cli_utils.hapless")
def test_get_or_exit_non_existing(hapless_mock, capsys):
    with patch.object(hapless_mock, "get_hap", return_value=None) as get_hap_mock:
        with pytest.raises(SystemExit) as e:
            get_or_exit("hap-me")

        assert e.value.code == 1
        get_hap_mock.assert_called_once_with("hap-me")

        captured = capsys.readouterr()
        assert "No such hap: hap-me" in captured.out


@patch("hapless.cli_utils.hapless")
def test_get_or_exit_not_accessible(hapless_mock, capsys):
    hap_mock = Mock(owner="someone-else")
    prop_mock = PropertyMock(return_value=False)
    type(hap_mock).accessible = prop_mock
    with patch.object(hapless_mock, "get_hap", return_value=hap_mock) as get_hap_mock:
        with pytest.raises(SystemExit) as e:
            get_or_exit("hap-not-mine")

        assert e.value.code == 1
        get_hap_mock.assert_called_once_with("hap-not-mine")
        prop_mock.assert_called_once_with()

        captured = capsys.readouterr()
        assert (
            "Cannot manage hap launched by another user. Owner: someone-else"
            in captured.out
        )
