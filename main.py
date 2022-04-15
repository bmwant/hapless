import os
import time
import tempfile
from pathlib import Path


import psutil
import humanize
from rich import box
from rich.console import Console
from rich.table import Table



"""
paused
running
failed
completed
"""

class Hap(object):
    def __init__(self, hap_path: Path):
        self.name = 'hap-name'
        self._hid = os.path.basename(hap_path)
        pid_file = hap_path / 'pid'
        with open(pid_file) as f:
            pid = f.read()
        self._pid = int(pid)

    @property
    def hid(self):
        return self._hid

    @property
    def pid(self):
        return self._pid


class Hapless(object):
    def __init__(self):
        pass

    @staticmethod
    def stats(haps):
        console = Console()
        table = Table(show_header=True, header_style="bold magenta", box=box.HEAVY_EDGE)
        table.add_column("#", style="dim", width=2)
        table.add_column("Name")
        table.add_column("PID")
        table.add_column("Status")
        table.add_column("Runtime", justify="right")

        for hap in haps:
            table.add_row(Hapless._stat_hap(hap))
        
        console.print(table)

    @staticmethod
    def _stat_hap(hap):
        try:
            p = psutil.Process(hap.pid)
            runtime = time.time() - p.create_time()
            return (
                f'{hap.hid}', 
                f'{hap.name}', 
                f'{hap.pid}',
                p.status(), 
                humanize.naturaldelta(runtime),
            )
        except psutil.NoSuchProcess:
            return (
                f'{hap.hid}',
                f'{hap.name}',
                f'{hap.pid}', 
                'completed',
                '1 h',
            )

    def get_haps(self):
        tmp_dir = Path(tempfile.gettempdir())
        hapless_dir = tmp_dir / 'hapless'
        haps = []
        for item in os.listdir(hapless_dir):
            hap_path = hapless_dir / item
            haps.append(Hap(hap_path))
        return haps


def main():
    h = Hapless()
    haps = h.get_haps()
    h.stats(haps)


if __name__ == '__main__':
    main()
