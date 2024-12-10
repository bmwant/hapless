from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from hapless.hap import Hap
from hapless.main import Hapless


@pytest.fixture
def runner() -> Generator[CliRunner, None, None]:
    cli_runner = CliRunner()
    with cli_runner.isolated_filesystem() as path:
        hapless_test = Hapless(hapless_dir=Path(path))
        with patch("hapless.cli.hapless", hapless_test) as hapless_mock:
            cli_runner.hapless = hapless_mock
            yield cli_runner


@pytest.fixture
def hap(tmpdir) -> Generator[Hap, None, None]:
    hapless = Hapless(hapless_dir=Path(tmpdir))
    yield hapless.create_hap("false")


@pytest.fixture
def hapless(tmpdir) -> Generator[Hapless, None, None]:
    yield Hapless(hapless_dir=Path(tmpdir))
