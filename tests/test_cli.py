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
    status_mock.assert_called_once_with()


@patch("hapless.cli._status")
def test_show_command_invokes_status(status_mock, runner):
    result = runner.invoke(cli.cli, ["show", "hap-me"])

    assert result.exit_code == 0
    status_mock.assert_called_once_with("hap-me", False)


@patch("hapless.cli._status")
def test_status_command_invokes_status(status_mock, runner):
    result = runner.invoke(cli.cli, ["status", "hap-me"])

    assert result.exit_code == 0
    status_mock.assert_called_once_with("hap-me", False)


def test_logs_invocation(runner):
    pass


def test_run_invocation(runner):
    pass


def test_clean_invocation(runner):
    with patch.object(runner.hapless, "clean") as clean_mock:
        result = runner.invoke(cli.cli, ["clean", "--skip-failed"])
        assert result.exit_code == 0
        clean_mock.assert_called_once_with(True)
