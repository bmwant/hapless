from unittest.mock import Mock, patch

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
    status_mock.assert_called_once_with(None, verbose=False)


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


@patch("hapless.cli.get_or_exit")
def test_logs_invocation(get_or_exit_mock, runner):
    hap_mock = Mock()
    get_or_exit_mock.return_value = hap_mock
    with patch.object(runner.hapless, "logs") as logs_mock:
        result = runner.invoke(cli.cli, ["logs", "hap-me", "--follow"])
        assert result.exit_code == 0
        get_or_exit_mock.assert_called_once_with("hap-me")
        logs_mock.assert_called_once_with(hap_mock, follow=True)


def test_run_invocation(runner):
    with patch.object(runner.hapless, "run") as run_mock:
        result = runner.invoke(cli.cli, ["run", "script", "--check"])
        assert result.exit_code == 0
        run_mock.assert_called_once_with("script", name=None, check=True)


def test_run_invocation_with_arguments(runner):
    with patch.object(runner.hapless, "run") as run_mock:
        result = runner.invoke(
            cli.cli, ["run", "--check", "--", "script", "--script-param"]
        )
        assert result.exit_code == 0
        run_mock.assert_called_once_with("script --script-param", name=None, check=True)


def test_run_invocation_name_provided(runner):
    with patch.object(runner.hapless, "run") as run_mock:
        result = runner.invoke(
            cli.cli, ["run", "--name", "hap-name", "--", "script", "--script-param"]
        )
        assert result.exit_code == 0
        run_mock.assert_called_once_with(
            "script --script-param", name="hap-name", check=False
        )


def test_clean_invocation(runner):
    with patch.object(runner.hapless, "clean") as clean_mock:
        result = runner.invoke(cli.cli, ["clean", "--skip-failed"])
        assert result.exit_code == 0
        clean_mock.assert_called_once_with(True)


@patch("hapless.cli.get_or_exit")
def test_kill_invocation(get_or_exit_mock, runner):
    hap_mock = Mock()
    get_or_exit_mock.return_value = hap_mock
    with patch.object(runner.hapless, "kill") as kill_mock:
        result = runner.invoke(cli.cli, ["kill", "hap-name"])
        assert result.exit_code == 0
        get_or_exit_mock.assert_called_once_with("hap-name")
        kill_mock.assert_called_once_with([hap_mock])


def test_killall_invocation(runner):
    pass


def test_killall_improper_invocation(runner):
    pass
