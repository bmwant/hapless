import logging
import shlex
import signal
import time
from functools import wraps
from pathlib import Path

import click

from hapless import config

logging.disable(level=logging.CRITICAL)

if config.DEBUG:
    logging.disable(logging.NOTSET)
    logging.basicConfig(level=logging.DEBUG)


logger = logging.getLogger(__package__)


def allow_missing(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            pass

    return wrapper


def shlex_join_backport(split_command):
    """Return a shell-escaped string"""
    return " ".join(shlex.quote(arg) for arg in split_command)


class timed(object):
    def __init__(self):
        self._start = time.time()
        self._end = None

    @property
    def elapsed(self):
        if self._end is not None:
            return self._end - self._start

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._end = time.time()
        return self


def wait_created(
    path: Path, interval: float = 0.1, timeout: float = config.FAILFAST_DELAY
):
    start = time.time()
    while not path.exists() and time.time() - start < timeout:
        time.sleep(interval)
    return path.exists()


def validate_signal(ctx, param, value):
    try:
        signal_code = int(value)
    except ValueError:
        raise click.BadParameter("Signal should be a valid integer value")

    try:
        return signal.Signals(signal_code)
    except ValueError:
        raise click.BadParameter(f"{signal_code} is not a valid signal code")
