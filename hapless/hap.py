import json
import os
import random
import string
import time
from pathlib import Path
from typing import Dict, Optional

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

    def _set_pid(self, pid: int):
        if not psutil.pid_exists(pid):
            raise ValueError(f"Cannot attach, pid {pid} doesn't exist")

        with open(self._pid_file, "w") as pid_file:
            pid_file.write(f"{pid}")

    def _set_env(self):
        proc = self.proc
        if proc is None:
            raise RuntimeError("Cannot get environment for the non-running process")

        with open(self._env_file, "w") as env_file:
            env_file.write(json.dumps(proc.environ()))

    def attach(self, pid: int):
        """
        Associate hap object with existing process by pid
        """
        self._set_pid(pid)
        self._set_env()

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
    def env(self) -> Dict[str, str]:
        proc = self.proc
        if proc is not None:
            return proc.environ()

        with open(self._env_file) as env_file:
            return json.loads(env_file.read())

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

    def __rich__(self) -> str:
        pid_text = f"with PID [[{config.COLOR_MAIN} bold]{self.pid}[/]]"
        rich_text = (
            f"hap {config.ICON_HAP}{self.hid} "
            f"([{config.COLOR_MAIN} bold]{self.name}[/])"
        )
        if self.pid:
            return f"{rich_text} {pid_text}"
        return rich_text
