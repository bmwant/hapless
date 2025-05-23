from contextlib import ExitStack
from unittest.mock import Mock, patch, MagicMock # Added MagicMock
import json # Added json
from hapless.hap import Status # Added Status

from hapless import cli


# Helper for Mock Hap Data (as per subtask description)
def create_mock_hap_dict(hid, name, status_val, verbose=False, pid=123, cmd="sleep 1"):
    data = {
        'hid': str(hid), 'name': name, 'raw_name': name, 'pid': pid, 'cmd': cmd.split(),
        'status': status_val, 'rc': 0 if status_val == Status.SUCCESS.value else None,
        'runtime': '1 second', 'restarts': 0, 'active': status_val == Status.RUNNING.value,
        'owner': 'testuser', 'start_time': '2023-01-01T00:00:00', 'end_time': None,
        'stdout_path': f'/tmp/hapless/{hid}/stdout.log', 'stderr_path': f'/tmp/hapless/{hid}/stderr.log',
        'path': f'/tmp/hapless/{hid}'
    }
    if verbose:
        data.update({'cwd': '/tmp', 'ppid': 1, 'user': 'testuser', 'env': {'TEST': 'VAR'}})
    return data


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
    status_mock.assert_called_once_with(None, verbose=False, json_output=False) # Modified


@patch("hapless.cli._status")
def test_show_command_invokes_status(status_mock, runner):
    result = runner.invoke(cli.cli, ["show", "hap-me"])

    assert result.exit_code == 0
    status_mock.assert_called_once_with("hap-me", False, json_output=False) # Modified


@patch("hapless.cli._status")
def test_status_command_invokes_status(status_mock, runner):
    result = runner.invoke(cli.cli, ["status", "hap-me"])

    assert result.exit_code == 0
    status_mock.assert_called_once_with("hap-me", False, json_output=False) # Modified


@patch("hapless.cli.get_or_exit")
def test_logs_invocation(get_or_exit_mock, runner):
    hap_mock = MagicMock(spec=cli.Hap) # Using MagicMock for spec
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


# --- Tests for JSON Output ---

@patch.object(cli.hapless, "get_haps")
def test_status_json_output_multiple_haps(get_haps_mock, runner):
    mock_hap1_data = create_mock_hap_dict(1, 'hap1', Status.RUNNING.value)
    mock_hap2_data = create_mock_hap_dict(2, 'hap2', Status.SUCCESS.value)

    mock_hap1 = MagicMock(spec=cli.Hap)
    mock_hap1.to_dict.return_value = mock_hap1_data
    mock_hap1.accessible = True # Assuming get_haps filters by accessible if not False

    mock_hap2 = MagicMock(spec=cli.Hap)
    mock_hap2.to_dict.return_value = mock_hap2_data
    mock_hap2.accessible = True

    get_haps_mock.return_value = [mock_hap1, mock_hap2]

    result = runner.invoke(cli.cli, ["status", "--json"])
    assert result.exit_code == 0

    output_data = json.loads(result.output)
    assert isinstance(output_data, list)
    assert len(output_data) == 2
    assert output_data[0]['name'] == 'hap1'
    assert output_data[0]['status'] == Status.RUNNING.value
    assert output_data[1]['name'] == 'hap2'
    assert output_data[1]['status'] == Status.SUCCESS.value

    mock_hap1.to_dict.assert_called_once_with(verbose=False)
    mock_hap2.to_dict.assert_called_once_with(verbose=False)
    get_haps_mock.assert_called_once_with(accessible_only=False) # _status calls get_haps with accessible_only=False


@patch.object(cli, "get_or_exit") # Patching get_or_exit directly for single hap scenarios
def test_status_json_output_single_hap(get_or_exit_mock, runner):
    mock_hap1_data = create_mock_hap_dict(1, 'hap1', Status.RUNNING.value)
    mock_hap1 = MagicMock(spec=cli.Hap)
    mock_hap1.to_dict.return_value = mock_hap1_data
    get_or_exit_mock.return_value = mock_hap1

    result = runner.invoke(cli.cli, ["status", "hap1", "--json"])
    assert result.exit_code == 0

    output_data = json.loads(result.output)
    assert isinstance(output_data, dict)
    assert output_data['name'] == 'hap1'
    assert output_data['status'] == Status.RUNNING.value
    assert 'env' not in output_data # Simple by default

    mock_hap1.to_dict.assert_called_once_with(verbose=False)
    get_or_exit_mock.assert_called_once_with("hap1")


@patch.object(cli, "get_or_exit")
def test_status_json_output_single_hap_verbose(get_or_exit_mock, runner):
    mock_hap1_data = create_mock_hap_dict(1, 'hap1', Status.RUNNING.value, verbose=True)
    mock_hap1 = MagicMock(spec=cli.Hap)
    mock_hap1.to_dict.return_value = mock_hap1_data
    get_or_exit_mock.return_value = mock_hap1

    result = runner.invoke(cli.cli, ["status", "hap1", "--json", "--verbose"])
    assert result.exit_code == 0

    output_data = json.loads(result.output)
    assert isinstance(output_data, dict)
    assert output_data['name'] == 'hap1'
    assert output_data['status'] == Status.RUNNING.value
    assert 'env' in output_data
    assert output_data['env'] == {'TEST': 'VAR'}

    mock_hap1.to_dict.assert_called_once_with(verbose=True)
    get_or_exit_mock.assert_called_once_with("hap1")


@patch.object(cli.hapless, "get_haps")
def test_main_command_json_output(get_haps_mock, runner):
    mock_hap1_data = create_mock_hap_dict(1, 'hap1', Status.RUNNING.value)
    mock_hap2_data = create_mock_hap_dict(2, 'hap2', Status.STOPPED.value)

    mock_hap1 = MagicMock(spec=cli.Hap)
    mock_hap1.to_dict.return_value = mock_hap1_data
    mock_hap1.accessible = True

    mock_hap2 = MagicMock(spec=cli.Hap)
    mock_hap2.to_dict.return_value = mock_hap2_data
    mock_hap2.accessible = True

    get_haps_mock.return_value = [mock_hap1, mock_hap2]

    result = runner.invoke(cli.cli, ["--json"]) # Main command: hapless --json
    assert result.exit_code == 0

    output_data = json.loads(result.output)
    assert isinstance(output_data, list)
    assert len(output_data) == 2
    assert output_data[0]['name'] == 'hap1'
    assert output_data[1]['name'] == 'hap2'

    mock_hap1.to_dict.assert_called_once_with(verbose=False) # Default no-command is not verbose
    mock_hap2.to_dict.assert_called_once_with(verbose=False)
    get_haps_mock.assert_called_once_with(accessible_only=False)


@patch.object(cli, "get_or_exit")
def test_show_json_output_single_hap(get_or_exit_mock, runner):
    mock_hap1_data = create_mock_hap_dict(1, 'hap1', Status.RUNNING.value, verbose=False) # show default is not verbose
    mock_hap1 = MagicMock(spec=cli.Hap)
    mock_hap1.to_dict.return_value = mock_hap1_data
    get_or_exit_mock.return_value = mock_hap1

    result = runner.invoke(cli.cli, ["show", "hap1", "--json"])
    assert result.exit_code == 0

    output_data = json.loads(result.output)
    assert isinstance(output_data, dict)
    assert output_data['name'] == 'hap1'
    assert 'env' not in output_data

    mock_hap1.to_dict.assert_called_once_with(verbose=False) # show command's default verbose is False
    get_or_exit_mock.assert_called_once_with("hap1")


@patch.object(cli, "get_or_exit")
def test_show_json_output_single_hap_verbose(get_or_exit_mock, runner):
    mock_hap1_data = create_mock_hap_dict(1, 'hap1', Status.RUNNING.value, verbose=True)
    mock_hap1 = MagicMock(spec=cli.Hap)
    mock_hap1.to_dict.return_value = mock_hap1_data
    get_or_exit_mock.return_value = mock_hap1

    result = runner.invoke(cli.cli, ["show", "hap1", "--json", "--verbose"])
    assert result.exit_code == 0

    output_data = json.loads(result.output)
    assert isinstance(output_data, dict)
    assert output_data['name'] == 'hap1'
    assert 'env' in output_data
    assert output_data['env'] == mock_hap1_data['env']

    mock_hap1.to_dict.assert_called_once_with(verbose=True)
    get_or_exit_mock.assert_called_once_with("hap1")
