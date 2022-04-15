import os
import asyncio
import sys
import tempfile
from pathlib import Path
from typing import List

from rich import box
from rich.console import Console
from rich.table import Table

from hapless.hap import Hap

"""
paused
running
finished
* finished(failed) non-zero rc
* finished(success) zero rc
"""

class Hapless(object):
    def __init__(self):
        tmp_dir = Path(tempfile.gettempdir())
        self._hapless_dir = tmp_dir / 'hapless'
        if not self._hapless_dir.exists():
            self._hapless_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def stats(haps: List[Hap]):
        console = Console()
        table = Table(show_header=True, header_style="bold magenta", box=box.HEAVY_EDGE)
        table.add_column("#", style="dim", width=2)
        table.add_column("Name")
        table.add_column("PID")
        table.add_column("Status")
        table.add_column("RC")
        table.add_column("Runtime", justify="right")

        for hap in haps:
            table.add_row(
                f'{hap.hid}',
                hap.name,
                f'{hap.pid}',
                hap.status,
                f'{hap.rc}',
                hap.runtime,
            )
        
        console.print(table)

    @staticmethod
    def show(hap: Hap):
        console = Console()
        table = Table(show_header=True, header_style="bold magenta", box=box.HEAVY_EDGE)
        table.add_column("#", style="dim", width=2)
        table.add_column("Name")
        table.add_column("PID")
        console.print(table)

    @property
    def dir(self) -> Path:
        return self._hapless_dir

    def _get_hap_dirs(self):  
        hap_dirs = filter(str.isdigit, os.listdir(self._hapless_dir))
        return sorted(hap_dirs)

    def get_next_hap_id(self):
        dirs = self._get_hap_dirs()
        return 1 if not dirs else int(dirs[-1]) + 1

    def get_hap(self, hap_alias) -> Hap:
        pass

    def get_haps(self) -> List[Hap]:
        haps = []
        if not self._hapless_dir.exists():
            return haps

        for dir in self._get_hap_dirs():
            hap_path = self._hapless_dir / dir
            haps.append(Hap(hap_path))
        return haps

    def run(self, cmd):
        hid = self.get_next_hap_id()
        hap_dir = self._hapless_dir / f'{hid}'
        hap_dir.mkdir()
        stdout_path = hap_dir / 'stdout.log'
        stderr_path = hap_dir / 'stderr.log'
        pid_path = hap_dir / 'pid'
        rc_path = hap_dir / 'rc'
        pid = os.fork()
        if pid == 0:
            coro = subprocess_wrapper(
                cmd,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                pid_path=pid_path,
                rc_path=rc_path,
            )   
            asyncio.run(coro)
        else:
            sys.exit(0)


async def subprocess_wrapper(
    cmd,
    *,
    stdout_path: Path,
    stderr_path: Path,
    pid_path: Path,
    rc_path: Path,
):
    with (
        open(stdout_path, 'w') as stdout_pipe,
        open(stderr_path, 'w') as stderr_pipe,
        open(rc_path, 'w') as rc_file,
    ):
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=stdout_pipe,
            stderr=stderr_pipe,
        )
        with open(pid_path, 'w') as pid_file:
            pid_file.write(f'{proc.pid}')

        _ = await proc.communicate()
        rc = proc.returncode
        rc_file.write(f'{rc}')
