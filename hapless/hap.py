import os
import random
import string
import time
from pathlib import Path
from typing import Optional

import humanize
import psutil

from hapless import config
from hapless.utils import allow_missing


class Hap(object):
    def __init__(
        self,
        hap_path: Path,
        *,
        name: Optional[str] = None,
        cmd: Optional[str] = None,
    ):
        self._hap_path = hap_path
        self._hid = os.path.basename(hap_path)

        self._pid_file = hap_path / "pid"
        self._rc_file = hap_path / "rc"
        self._name_file = hap_path / "name"
        self._cmd_file = hap_path / "cmd"
        self._env_file = hap_path / "env"

        self._set_name(name)
        self._set_cmd(cmd)
        self._set_env()

    def _set_name(self, name: Optional[str]):
        """
        Sets name for the first time on hap creation.
        """
        if name is None:
            suffix = self.get_random_name()
            name = f"hap-{suffix}"

        if self.name is None:
            with open(self._name_file, "w") as f:
                f.write(name)

    def _set_cmd(self, cmd: Optional[str]):
        """
        Sets cmd for the first tiem on hap creation.
        """
        if self.cmd is None:
            if cmd is None:
                raise ValueError("Command to run is not provided")
            with open(self._cmd_file, "w") as f:
                f.write(cmd)

    def _set_env(self):
        pass

    @staticmethod
    def get_random_name(length: int = 6):
        return "".join(
            random.sample(
                string.ascii_lowercase + string.digits,
                length,
            )
        )

    # todo: add extended status to show panel proc.status()
    @property
    def status(self) -> str:
        proc = self.proc
        # todo: running or paused
        if proc is not None:
            return f"{config.ICON_RUNNING} running"

        if self.rc != 0:
            return f"{config.ICON_FAILED} failed"

        return f"{config.ICON_SUCCESS} success"

    @property
    def proc(self):
        try:
            return psutil.Process(self.pid)
        except psutil.NoSuchProcess:
            pass

    @property
    @allow_missing
    def cmd(self) -> str:
        # todo: might be better for the shell expansion
        # shlex.join(proc.cmdline())
        with open(self._cmd_file) as f:
            return f.read()

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

    @property
    def path(self):
        return self._hap_path

    @property
    def stdout_path(self):
        return self._hap_path / "stdout.log"

    @property
    def stderr_path(self):
        return self._hap_path / "stderr.log"

    def __str__(self):
        return f"#{self.hid} ({self.name})"
