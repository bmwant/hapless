from contextlib import ExitStack
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
    status_mock.assert_called_once_with(None, verbose=False, json_output=False)


@patch("hapless.cli._status")
def test_show_command_invokes_status(status_mock, runner):
    result = runner.invoke(cli.cli, ["show", "hap-me"])

    assert result.exit_code == 0
    status_mock.assert_called_once_with("hap-me", False, False)


@patch("hapless.cli._status")
def test_status_command_invokes_status(status_mock, runner):
    result = runner.invoke(cli.cli, ["status", "hap-me"])

    assert result.exit_code == 0
    status_mock.assert_called_once_with("hap-me", False, json_output=False)


@patch("hapless.cli._status")
def test_status_accepts_json_argument(status_mock, runner):
    result = runner.invoke(cli.cli, ["status", "hap-me", "--json"])

    assert result.exit_code == 0
    status_mock.assert_called_once_with("hap-me", False, json_output=True)


@patch("hapless.cli.get_or_exit")
def test_logs_invocation(get_or_exit_mock, runner):
    hap_mock = Mock()
    get_or_exit_mock.return_value = hap_mock
    with patch.object(runner.hapless, "logs") as logs_mock:
        result = runner.invoke(cli.cli, ["logs", "hap-me", "--follow"])
        assert result.exit_code == 0
        get_or_exit_mock.assert_called_once_with("hap-me")
        logs_mock.assert_called_once_with(hap_mock, stderr=False, follow=True)


@patch("hapless.cli.get_or_exit")
def test_logs_stderr_invocation(get_or_exit_mock, runner):
    hap_mock = Mock()
    get_or_exit_mock.return_value = hap_mock
    with patch.object(runner.hapless, "logs") as logs_mock:
        result = runner.invoke(cli.cli, ["logs", "hap-me", "--stderr"])
        assert result.exit_code == 0
        get_or_exit_mock.assert_called_once_with("hap-me")
        logs_mock.assert_called_once_with(hap_mock, stderr=True, follow=False)


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


def test_run_invocation_same_name_provided(runner):
    name = "hap-name"
    cmd = "script"
    with patch.object(runner.hapless, "run") as run_mock:
        result_pass = runner.invoke(cli.cli, ["run", "--name", name, cmd])
        assert result_pass.exit_code == 0
        run_mock.assert_called_once_with(
            cmd,
            name=name,
            check=False,
        )
        # make sure record for the hap has been actually created
        runner.hapless.create_hap(cmd=cmd, name=name)

        # call again with the same name
        result_fail = runner.invoke(cli.cli, ["run", "--name", name, cmd])
        assert result_fail.exit_code == 1
        assert run_mock.call_count == 1


def test_run_empty_invocation(runner):
    with patch.object(runner.hapless, "run") as run_mock:
        result = runner.invoke(cli.cli, "run  ")
        assert result.exit_code == 1
        assert "You have to provide a command to run" in result.output
        assert not run_mock.called


def test_clean_invocation(runner):
    with patch.object(runner.hapless, "clean") as clean_mock:
        result = runner.invoke(cli.cli, ["clean", "--all"])
        assert result.exit_code == 0
        clean_mock.assert_called_once_with(clean_all=True)


def test_cleanall_invocation(runner):
    with patch.object(runner.hapless, "clean") as clean_mock:
        result = runner.invoke(cli.cli, ["cleanall"])
        assert result.exit_code == 0
        clean_mock.assert_called_once_with(clean_all=True)


@patch("hapless.cli.get_or_exit")
def test_pause_invocation(get_or_exit_mock, runner):
    hap_mock = Mock()
    get_or_exit_mock.return_value = hap_mock
    with patch.object(runner.hapless, "pause_hap") as pause_mock:
        result = runner.invoke(cli.cli, ["pause", "hap-me"])
        assert result.exit_code == 0
        get_or_exit_mock.assert_called_once_with("hap-me")
        pause_mock.assert_called_once_with(hap_mock)


@patch("hapless.cli.get_or_exit")
def test_resume_invocation(get_or_exit_mock, runner):
    hap_mock = Mock()
    get_or_exit_mock.return_value = hap_mock
    with patch.object(runner.hapless, "resume_hap") as resume_mock:
        result = runner.invoke(cli.cli, ["resume", "hap-me"])
        assert result.exit_code == 0
        get_or_exit_mock.assert_called_once_with("hap-me")
        resume_mock.assert_called_once_with(hap_mock)


@patch("hapless.cli.get_or_exit")
def test_restart_invocation(get_or_exit_mock, runner):
    hap_mock = Mock()
    get_or_exit_mock.return_value = hap_mock
    with patch.object(runner.hapless, "restart") as restart_mock:
        result = runner.invoke(cli.cli, ["restart", "hap-me"])
        assert result.exit_code == 0
        get_or_exit_mock.assert_called_once_with("hap-me")
        restart_mock.assert_called_once_with(hap_mock)


@patch("hapless.cli.get_or_exit")
def test_rename_invocation(get_or_exit_mock, runner):
    hap_mock = Mock()
    get_or_exit_mock.return_value = hap_mock
    with patch.object(runner.hapless, "rename_hap") as rename_mock:
        result = runner.invoke(cli.cli, ["rename", "hap-me", "new-hap-name"])
        assert result.exit_code == 0
        get_or_exit_mock.assert_called_once_with("hap-me")
        rename_mock.assert_called_once_with(hap_mock, "new-hap-name")


@patch("hapless.cli.get_or_exit")
def test_rename_name_exists(get_or_exit_mock, runner):
    hap_mock = Mock()
    other_hap = Mock()
    get_or_exit_mock.return_value = hap_mock
    # NOTE: Python 3.7/3.8 compatibility
    with ExitStack() as stack:
        rename_mock = stack.enter_context(patch.object(runner.hapless, "rename_hap"))
        get_hap_mock = stack.enter_context(
            patch.object(runner.hapless, "get_hap", return_value=other_hap)
        )

        result = runner.invoke(cli.cli, ["rename", "hap-me", "new-hap-name"])
        assert result.exit_code == 1
        assert "Hap with such name already exists" in result.output
        get_or_exit_mock.assert_called_once_with("hap-me")
        get_hap_mock.assert_called_once_with("new-hap-name")
        rename_mock.assert_not_called()
