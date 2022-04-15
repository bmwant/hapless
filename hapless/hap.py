import os
import time
from pathlib import Path

import psutil
import humanize


class Hap(object):
    def __init__(self, hap_path: Path):
        self._name = 'hap-name'
        self._hid = os.path.basename(hap_path)
        pid_file = hap_path / 'pid'
        with open(pid_file) as f:
            pid = f.read()
        self._pid = int(pid)
        self._proc = None
        # self._active = True
        try:
            self._proc = psutil.Process(self._pid)
        except psutil.NoSuchProcess:
            pass

    @property
    def status(self) -> str:
        if self._proc is not None:
            return self._proc.status()
        return 'completed'

    @property
    def runtime(self) -> str:
        if self._proc is not None:
            runtime = time.time() - self._proc.create_time()
            return humanize.naturaldelta(runtime)
        


    @property
    def active(self) -> bool:
        return self._proc is not None

    @property
    def hid(self) -> int:
        return self._hid

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def name(self) -> str:
        return self._name
