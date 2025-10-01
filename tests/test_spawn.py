from unittest.mock import Mock, PropertyMock, patch

import pytest

from hapless import cli
from hapless.hap import Status


@patch("hapless.cli.get_or_exit")
def test_internal_wrap_hap(get_or_exit_mock, runner):
    hap_mock = Mock(
        status=Status.UNBOUND,
    )
    prop_mock = PropertyMock()
    type(hap_mock).stderr_path = prop_mock
    get_or_exit_mock.return_value = hap_mock
    with patch.object(runner.hapless, "_wrap_subprocess") as wrap_mock:
        result = runner.invoke(cli.cli, ["__internal_wrap_hap", "hap-me"])
        assert result.exit_code == 0
        get_or_exit_mock.assert_called_once_with("hap-me")
        wrap_mock.assert_called_once_with(hap_mock)
        prop_mock.assert_not_called()


@patch("hapless.cli.get_or_exit")
def test_internal_wrap_hap_not_unbound(get_or_exit_mock, runner, tmp_path, log_output):
    hap_mock = Mock(
        status=Status.FAILED,
        __str__=lambda self: "hap-me",
    )
    prop_mock = PropertyMock(return_value=tmp_path / "stderr.log")
    type(hap_mock).stderr_path = prop_mock
    get_or_exit_mock.return_value = hap_mock
    with patch.object(runner.hapless, "_wrap_subprocess") as wrap_mock:
        result = runner.invoke(cli.cli, ["__internal_wrap_hap", "hap-me"])
        assert result.exit_code == 1
        get_or_exit_mock.assert_called_once_with("hap-me")
        prop_mock.assert_called_once_with()
        wrap_mock.assert_not_called()
        assert (
            "ERROR: Hap hap-me has to be unbound, found instead Status.FAILED"
            in log_output.text
        )


@patch("hapless.cli.get_or_exit")
@patch("hapless.cli.isatty")
def test_wrap_cannot_be_launched_interactively(
    isatty_mock, get_or_exit_mock, runner, log_output
):
    isatty_mock.return_value = True
    get_or_exit_mock.side_effect = lambda _: pytest.fail("Should not be called")
    with patch.object(runner.hapless, "_wrap_subprocess") as wrap_mock, patch(
        "hapless.config.DEBUG", False
    ):
        result = runner.invoke(cli.cli, ["__internal_wrap_hap", "hap-me"])
        assert result.exit_code == 1
        get_or_exit_mock.assert_not_called()
        wrap_mock.assert_not_called()
        assert (
            "CRITICAL: Internal command is not supposed to be run manually"
            in log_output.text
        )
