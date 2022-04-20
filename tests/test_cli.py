from unittest.mock import patch

from hapless import cli


def test_executable_invocation(runner):
    result = runner.invoke(cli.cli)

    assert result.exit_code == 0

    assert "No haps are currently running" in result.output


def test_version_invocation(runner):
    result = runner.invoke(cli.cli, ["--version"])

    assert result.exit_code == 0
    assert result.output.startswith("hapless, version")


def test_help_invocation(runner):
    result = runner.invoke(cli.cli, ["--help"])

    assert result.exit_code == 0
    assert "Show this message and exit" in result.output


@patch("hapless.cli._status")
def test_no_command_invokes_status(status_mock, runner):
    result = runner.invoke(cli.cli)

    assert result.exit_code == 0
    assert status_mock.called_once_with(None, False)


@patch("hapless.cli._status")
def test_show_command_invokes_status(status_mock, runner):
    result = runner.invoke(cli.cli, ["show", "hap-me"])

    assert result.exit_code == 0
    assert status_mock.called_once_with("hap-me", False)


@patch("hapless.cli._status")
def test_status_command_invokes_status(status_mock, runner):
    result = runner.invoke(cli.cli, ["status", "hap-me"])

    assert result.exit_code == 0
    assert status_mock.called_once_with("hap-me", False)
