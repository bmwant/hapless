from unittest.mock import patch

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
