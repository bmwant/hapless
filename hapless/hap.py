import os
import shlex
import time
from functools import wraps
from pathlib import Path
from typing import Optional

import humanize
import psutil


def allow_missing(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            pass

    return wrapper


class Hap(object):
    def __init__(self, hap_path: Path, *, name: Optional[str] = None):
        self._hap_path = hap_path
        self._hid = os.path.basename(hap_path)

        # todo: allow overrides?
        self._pid_file = hap_path / "pid"
        self._rc_file = hap_path / "rc"
        self._name_file = hap_path / "name"
        self._cmd_file = hap_path / "cmd"
        self._env_file = hap_path / "env"

        self._set_name(name)

    def _set_name(self, name: Optional[str]):
        """
        Sets name for the first time on hap creation.
        """
        if name is None:
            name = "generated-random"

        if self.name is None:
            with open(self._name_file, "w") as f:
                f.write(name)

    @property
    def status(self) -> str:
        proc = self.proc
        if proc is not None:
            return proc.status()
        return "success"

    @property
    def proc(self):
        try:
            return psutil.Process(self.pid)
        except psutil.NoSuchProcess:
            pass

    @property
    def cmd(self) -> str:
        proc = self.proc
        if proc is not None:
            return shlex.join(proc.cmdline())
        return "python fallback_cmd.py --finished"

    @property
    @allow_missing
    def rc(self) -> Optional[int]:
        with open(self._rc_file) as f:
            return int(f.read())

    @property
    def runtime(self) -> str:
        proc = self.proc
        if proc is not None:
            runtime = time.time() - proc.create_time()
        else:
            start_time = os.path.getmtime(self._pid_file)
            finish_time = os.path.getmtime(self._rc_file)
            runtime = finish_time - start_time

        return humanize.naturaldelta(runtime)

    @property
    def active(self) -> bool:
        return self.proc is not None

    @property
    def hid(self) -> int:
        return self._hid

    @property
    @allow_missing
    def pid(self) -> Optional[int]:
        with open(self._pid_file) as f:
            return int(f.read())

    @property
    @allow_missing
    def env(self):
        pass

    @property
    @allow_missing
    def name(self) -> Optional[str]:
        with open(self._name_file) as f:
            return f.read().strip()
