import logging
import os
import shlex
import signal
import time
from contextlib import nullcontext
from functools import wraps
from pathlib import Path
from typing import Optional

import click
import psutil
import structlog
from rich.spinner import Spinner
from rich.text import Text

from hapless import config


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


class dummy_live(nullcontext):
    def update(self, *args, **kwargs):
        pass


def wait_created(
    path: Path,
    interval: float = 0.1,
    timeout: float = config.FAILFAST_TIMEOUT,
    *,
    live_context=dummy_live(),
) -> bool:
    start = time.time()
    with live_context:
        elapsed = 0
        while not path.exists() and elapsed < timeout:
            elapsed = time.time() - start
            spinner = Spinner(
                "dots",
                text=Text.from_markup(
                    f"checking process health for "
                    f"[bold {config.COLOR_MAIN}]{int(timeout - elapsed)}s[/]..."
                ),
                style=f"{config.COLOR_MAIN}",
            )
            live_context.update(spinner)
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


def kill_proc_tree(pid, sig=signal.SIGKILL, include_parent=True):
    if pid == os.getpid():
        raise ValueError("Would not kill myself")

    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    if include_parent:
        children.append(parent)
    for p in children:
        try:
            p.send_signal(sig)
            logger.debug(f"Sent {sig} to {p.pid} process")
        except psutil.NoSuchProcess:
            pass


def get_mtime(path: Path) -> Optional[float]:
    if path.exists():
        return os.path.getmtime(path)


def configure_logger() -> logging.Logger:
    logger = structlog.get_logger()
    level = logging.DEBUG if config.DEBUG else logging.CRITICAL
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(level))
    return logger


logger = configure_logger()
