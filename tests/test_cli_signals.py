from unittest.mock import Mock, patch

from hapless import cli


@patch("hapless.cli.get_or_exit")
def test_kill_invocation(get_or_exit_mock, runner):
    hap_mock = Mock()
    get_or_exit_mock.return_value = hap_mock
    with patch.object(runner.hapless, "kill") as kill_mock:
        result = runner.invoke(cli.cli, ["kill", "hap-name"])
        assert result.exit_code == 0
        get_or_exit_mock.assert_called_once_with("hap-name")
        kill_mock.assert_called_once_with([hap_mock])


@patch("hapless.cli.get_or_exit")
def test_killall_invocation(get_or_exit_mock, runner):
    with patch.object(runner.hapless, "get_haps", return_value=[]) as get_haps_mock:
        with patch.object(runner.hapless, "kill") as kill_mock:
            result = runner.invoke(cli.cli, ["kill", "--all"])
            assert result.exit_code == 0
            get_or_exit_mock.assert_not_called()
            get_haps_mock.assert_called_once_with()
            kill_mock.assert_called_once_with([])


def test_kill_improper_invocation(runner):
    with patch.object(runner.hapless, "kill") as kill_mock:
        result = runner.invoke(cli.cli, ["kill"])
        assert result.exit_code == 2
        assert "Provide hap alias to kill" in result.stdout
        kill_mock.assert_not_called()


def test_killall_improper_invocation(runner):
    with patch.object(runner.hapless, "kill") as kill_mock:
        result = runner.invoke(cli.cli, ["kill", "hap-name", "-a"])
        assert result.exit_code == 2
        assert "Cannot use --all flag while hap id provided" in result.stdout
        kill_mock.assert_not_called()


@patch("hapless.cli.get_or_exit")
def test_signal_invocation(get_or_exit_mock, runner):
    hap_mock = Mock()
    get_or_exit_mock.return_value = hap_mock
    with patch.object(runner.hapless, "signal") as signal_mock:
        result = runner.invoke(cli.cli, ["signal", "hap-name", "9"])
        assert result.exit_code == 0
        get_or_exit_mock.assert_called_once_with("hap-name")
        signal_mock.assert_called_once_with(hap_mock, 9)


def test_signal_invalid_hap():
    pass


def test_signal_wrong_code():
    pass


def test_signal_inactive_hap():
    pass
