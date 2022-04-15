import os
import tempfile
from pathlib import Path

from rich import box
from rich.console import Console
from rich.table import Table

from hapless.hap import Hap

"""
paused
running
failed
completed
"""

class Hapless(object):
    def __init__(self):
        tmp_dir = Path(tempfile.gettempdir())
        self._hapless_dir = tmp_dir / 'hapless'
        if not self._hapless_dir.exists():
            self._hapless_dir.mkdir(parents=True, exist_ok=True)

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
            table.add_row(
                f'{hap.hid}',
                hap.name,
                f'{hap.pid}',
                hap.status,
                hap.runtime,
            )
        
        console.print(table)

    def _get_hap_dirs(self):  
        hap_dirs = filter(str.isdigit, os.listdir(self._hapless_dir))
        return sorted(hap_dirs)

    def get_next_hap_id(self):
        dirs = self._get_hap_dirs()
        return 1 if not dirs else int(dirs[-1]) + 1

    def get_haps(self):
        haps = []
        if not self._hapless_dir.exists():
            return haps

        for dir in self._get_hap_dirs():
            hap_path = self._hapless_dir / dir
            haps.append(Hap(hap_path))
        return haps


def main():
    h = Hapless()
    print(h.get_next_hap_id())
    haps = h.get_haps()
    h.stats(haps)


if __name__ == '__main__':
    main()
