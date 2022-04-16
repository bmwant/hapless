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
