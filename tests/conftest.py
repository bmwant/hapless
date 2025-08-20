import logging
import os
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
import structlog
from click.testing import CliRunner
from structlog import testing

from hapless.hap import Hap
from hapless.main import Hapless


class LogCapture(testing.LogCapture):
    @property
    def text(self) -> str:
        return "\n".join(
            f"{entry['log_level'].upper()}: {entry['event']}" for entry in self.entries
        )


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
def hapless(tmpdir, monkeypatch) -> Generator[Hapless, None, None]:
    monkeypatch.chdir(tmpdir)
    yield Hapless(hapless_dir=Path(tmpdir), quiet=True)


@pytest.fixture(name="log_output")
def structlog_log_output():
    log_capture = LogCapture()
    structlog.configure(
        processors=[log_capture],
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
    )
    return log_capture
