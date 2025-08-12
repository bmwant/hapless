import json
import os
import pwd
import random
import string
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

try:
    from functools import cached_property
except ImportError:
    # Fallback for Python 3.7
    from backports.cached_property import cached_property

import humanize
import psutil

from hapless import config
from hapless.utils import allow_missing, get_mtime, logger


class Status(str, Enum):
    # Active statuses
    UNBOUND = "unbound"
    PAUSED = "paused"
    RUNNING = "running"
    # Finished statuses
    FAILED = "failed"
    SUCCESS = "success"


class Hap(object):
    def __init__(
        self,
        hap_path: Path,
        *,
        name: Optional[str] = None,
        cmd: Optional[str] = None,
        stdout_filepath: Optional[Path] = None,
        stderr_filepath: Optional[Path] = None,
        redirect_stderr: bool = False,
    ) -> None:
        if not hap_path.is_dir():
            raise ValueError(f"Path {hap_path} is not a directory")

        self._hap_path = hap_path
        self._hid: str = hap_path.name

        self._pid_file = hap_path / "pid"
        self._rc_file = hap_path / "rc"
        self._name_file = hap_path / "name"
        self._cmd_file = hap_path / "cmd"
        self._env_file = hap_path / "env"

        self._stdout_path = stdout_filepath or (hap_path / "stdout.log")
        self._stderr_path = stderr_filepath or (hap_path / "stderr.log")
        self._redirect_stderr = redirect_stderr

        self._set_raw_name(name)
        self._set_cmd(cmd)

    def set_name(self, name: str):
        with open(self._name_file, "w") as f:
            f.write(name)

    def _set_raw_name(self, raw_name: Optional[str]):
        """
        Set name for the first time on hap creation.
        """
        if raw_name is None:
            suffix = self.get_random_name()
            raw_name = f"hap-{suffix}"

        if self.raw_name is None:
            self.set_name(raw_name)

    def _set_cmd(self, cmd: Optional[str]):
        """
        Set cmd for the first time on hap creation.
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

    def bind(self, pid: int):
        """
        Associate hap object with existing process by pid
        """
        try:
            self._set_pid(pid)
            self._set_env()
        except (RuntimeError, psutil.AccessDenied) as e:
            logger.error(f"Cannot bind due to {e}")

    @staticmethod
    def get_random_name(length: int = 6) -> str:
        return "".join(
            random.sample(
                string.ascii_lowercase + string.digits,
                length,
            )
        )

    # TODO: add extended status to show panel proc.status()
    @property
    def status(self) -> Status:
        if self.pid is None and self.rc is None:
            # No existing process or no return code from the finished one
            return Status.UNBOUND

        proc = self.proc
        if proc is not None:
            if proc.status() == psutil.STATUS_STOPPED:
                return Status.PAUSED
            return Status.RUNNING

        if self.rc != 0:
            return Status.FAILED

        return Status.SUCCESS

    @cached_property
    def proc(self):
        # NOTE: this is cached for the instance lifetime, fits our use case
        if self.pid is None:
            return

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
        runtime = 0
        if proc is not None:
            runtime = time.time() - proc.create_time()
        elif self._pid_file.exists():
            start_time = get_mtime(self._pid_file)
            finish_time = get_mtime(self._rc_file) or get_mtime(self.stderr_path)
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
    def hid(self) -> str:
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
    def raw_name(self) -> Optional[str]:
        with open(self._name_file) as f:
            return f.read().strip()

    @cached_property
    def name(self) -> str:
        """
        Base name without restarts counter.
        """
        return self.raw_name.split(config.RESTART_DELIM)[0]

    @cached_property
    def restarts(self) -> int:
        _, *rest = self.raw_name.rsplit("@", maxsplit=1)
        return int(rest[0]) if rest else 0

    @property
    def path(self) -> Path:
        return self._hap_path

    @property
    def stdout_path(self) -> Path:
        return self._stdout_path

    @property
    def stderr_path(self) -> Path:
        return self._stdout_path if self._redirect_stderr else self._stderr_path

    @property
    def accessible(self) -> bool:
        """
        Check if current user has control over the hap.
        """
        try:
            os.utime(self.path)
            return True
        except PermissionError:
            return False

    @property
    def owner(self) -> str:
        stat = self.path.stat()
        try:
            owner = pwd.getpwuid(stat.st_uid).pw_name
        except KeyError:
            owner = f"{stat.st_uid}:{stat.st_gid}"
        return owner

    def serialize(self) -> dict:
        """
        Serialize hap object into a dictionary.
        """
        return {
            "hid": self.hid,
            "name": self.name,
            "pid": str(self.pid) if self.pid is not None else None,
            "rc": str(self.rc) if self.rc is not None else None,
            "cmd": self.cmd,
            "status": self.status.value,
            "runtime": self.runtime,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "restarts": str(self.restarts),
            "stdout_file": str(self.stdout_path),
            "stderr_file": str(self.stderr_path),
        }

    def __str__(self) -> str:
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
