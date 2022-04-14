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

        for h in haps:
            try:
                p = psutil.Process(h.pid)
                runtime = time.time() - p.create_time()
                table.add_row(f'{h.hid}', f'{h.name}', f'{h.pid}', p.status(), humanize.naturaldelta(runtime))
            except psutil.NoSuchProcess:
                table.add_row(f'{h.hid}', f'{h.name}', f'{h.pid}', 'completed', '1 h')
        
        console.print(table)

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
