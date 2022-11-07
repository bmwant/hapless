import json
import os
import random
import string
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import humanize
import psutil

from hapless import config
from hapless.utils import allow_missing, logger

"""
active
* paused
* running
finished
* finished(failed) non-zero rc
* finished(success) zero rc
"""


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
        with open(self._pid_file, "w") as pid_file:
            pid_file.write(f"{pid}")

        if not psutil.pid_exists(pid):
            raise RuntimeError(f"Process with pid {pid} is gone")

    def _set_env(self):
        proc = self.proc

        environ = {}
        if proc is not None:
            environ = proc.environ()

        if not environ:
            logger.warning(
                "Cannot get environment from the process. "
                "Fallback to current environment"
            )
            environ = dict(os.environ)

        with open(self._env_file, "w") as env_file:
            env_file.write(json.dumps(environ))

    def attach(self, pid: int):
        """
        Associate hap object with existing process by pid
        """
        try:
            self._set_pid(pid)
            self._set_env()
        except (RuntimeError, psutil.AccessDenied) as e:
            logger.error(f"Cannot attached due to {e}")

    @staticmethod
    def get_random_name(length: int = 6):
        return "".join(
            random.sample(
                string.ascii_lowercase + string.digits,
                length,
            )
        )

    # TODO: add extended status to show panel proc.status()
    # TODO: return enum entries instead
    @property
    def status(self) -> str:
        proc = self.proc
        if proc is not None:
            if proc.status() == psutil.STATUS_STOPPED:
                return "paused"
            return "running"

        if self.rc != 0:
            return "failed"

        return "success"

    @property
    def proc(self):
        try:
            return psutil.Process(self.pid)
        except psutil.NoSuchProcess as e:
            logger.warning(f"Cannot find process: {e}")

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
    def start_time(self) -> Optional[str]:
        if self._pid_file.exists():
            return datetime.fromtimestamp(os.path.getmtime(self._pid_file)).strftime(
                config.DATETIME_FORMAT
            )
        logger.info("No start time as hap has not started yet")

    @property
    def end_time(self) -> Optional[str]:
        if self._rc_file.exists():
            return datetime.fromtimestamp(os.path.getmtime(self._rc_file)).strftime(
                config.DATETIME_FORMAT
            )
        logger.info("No end time as hap has not finished yet")

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
