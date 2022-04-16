import os
import time
from pathlib import Path
from typing import Optional

import humanize
import psutil


class Hap(object):
    def __init__(self, hap_path: Path):
        self._name = "hap-name"
        self._hap_path = hap_path
        self._hid = os.path.basename(hap_path)

        # todo: allow overrides
        self._pid_file = hap_path / "pid"
        self._rc_file = hap_path / "rc"

    @property
    def status(self) -> str:
        proc = self.proc
        if proc is not None:
            return proc.status()
        return "completed"

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
            return proc.cmdline()
        return "python fallback_cmd.py --finished"

    @property
    def rc(self) -> Optional[int]:
        if self._rc_file.exists():
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
    def pid(self) -> Optional[int]:
        if self._pid_file.exists():
            with open(self._pid_file) as f:
                return int(f.read())

    @property
    def name(self) -> str:
        return self._name
