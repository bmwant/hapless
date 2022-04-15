import os
import time
from pathlib import Path

import psutil
import humanize


class Hap(object):
    def __init__(self, hap_path: Path):
        self._name = 'hap-name'
        self._hap_path = hap_path
        self._hid = os.path.basename(hap_path)

        # todo: allow overrides
        self._pid_file = hap_path / 'pid'
        self._rc_file = hap_path / 'rc'

    @property
    def status(self) -> str:
        proc = self.proc
        if proc is not None:
            return proc.status()
        return 'completed'

    @property
    def proc(self):
        try:
            return psutil.Process(self.pid)
        except psutil.NoSuchProcess:
            pass

    @property
    def rc(self) -> int:
        if self._rc_file.exists():
            with open(self._rc_file) as f:
                return int(f.read())

    @property
    def runtime(self) -> str:
        proc = self.proc
        if proc is not None:
            runtime = time.time() - proc.create_time()
        # todo: proper runtime for finished hap
        runtime = time.time() - os.path.getmtime(self._pid_file)
        return humanize.naturaldelta(runtime)

    @property
    def active(self) -> bool:
        return self.proc is not None

    @property
    def hid(self) -> int:
        return self._hid

    @property
    def pid(self) -> int:
        if self._pid_file.exists():
            with open(self._pid_file) as f:
                return int(f.read())

    @property
    def name(self) -> str:
        return self._name
