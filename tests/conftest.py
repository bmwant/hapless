import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    cli_runner = CliRunner()
    with cli_runner.isolated_filesystem():
        yield cli_runner
