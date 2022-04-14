import asyncio
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


def console():
    console = Console()

    table = Table(show_header=True, header_style="bold magenta", box=box.HEAVY_EDGE)
    table.add_column("#", style="dim", width=2)
    table.add_column("Name")
    table.add_column("PID")
    table.add_column("Status")
    table.add_column("Runtime", justify="right")

    # todo: add rc
    pids = [
        36800,
        7646,
        5044,
    ]
    for index, pid in enumerate(pids, 1):
        p = psutil.Process(pid)
        runtime = time.time() - p.create_time()
        table.add_row(str(index), "name", str(pid), p.status(), humanize.naturaldelta(runtime))

    console.print(table)


if __name__ == '__main__':
    console()
