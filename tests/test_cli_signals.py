import signal
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


def test_signal_invalid_hap(runner):
    with patch.object(runner.hapless, "signal") as signal_mock:
        result = runner.invoke(cli.cli, ["signal", "invalid-hap", "9"])
        assert result.exit_code == 1
        assert "No such hap" in result.stdout
        signal_mock.assert_not_called()


@patch("hapless.cli.get_or_exit")
def test_signal_wrong_code(get_or_exit_mock, runner):
    hap_mock = Mock()
    get_or_exit_mock.return_value = hap_mock
    wrong_code = f"{signal.NSIG}"
    with patch.object(runner.hapless, "signal") as signal_mock:
        result = runner.invoke(cli.cli, ["signal", "hap-name", wrong_code])
        assert result.exit_code == 2
        assert f"{wrong_code} is not a valid signal code" in result.stdout
        get_or_exit_mock.assert_not_called()
        signal_mock.assert_not_called()


@patch("hapless.cli.get_or_exit")
def test_signal_inactive_hap(get_or_exit_mock, runner):
    hap_mock = Mock(active=False)
    get_or_exit_mock.return_value = hap_mock
    result = runner.invoke(cli.cli, ["signal", "hap-name", "15"])
    assert result.exit_code == 0
    assert "Cannot send signal to the inactive hap" in result.stdout
    get_or_exit_mock.assert_called_once_with("hap-name")
