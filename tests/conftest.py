from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from hapless.main import Hapless


@pytest.fixture
def runner():
    cli_runner = CliRunner()
    with cli_runner.isolated_filesystem() as path:
        hapless_test = Hapless(hapless_dir=Path(path))
        with patch("hapless.cli.hapless", hapless_test) as hapless_mock:
            cli_runner.hapless = hapless_mock
            yield cli_runner
