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
            table.add_row(
                f'{hap.hid}',
                hap.name,
                f'{hap.pid}',
                hap.status,
                hap.runtime,
            )
        
        console.print(table)

    def get_haps(self):
        tmp_dir = Path(tempfile.gettempdir())
        hapless_dir = tmp_dir / 'hapless'
        haps = []
        if not hapless_dir.exists():
            return haps

        # todo: sort by ascending
        hap_dirs = filter(str.isdigit, os.listdir(hapless_dir))
        for dir in hap_dirs:
            hap_path = hapless_dir / dir
            haps.append(Hap(hap_path))
        return haps


def main():
    h = Hapless()
    haps = h.get_haps()
    h.stats(haps)


if __name__ == '__main__':
    main()
