import asyncio
import time
from datetime import datetime

import psutil
import humanize
from rich import box
from rich.console import Console
from rich.table import Table


async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        print(f'[stdout]\n{stdout.decode()}')
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')


"""
paused
running
failed
completed
"""

def main():
    console = Console()

    table = Table(show_header=True, header_style="bold magenta", box=box.HEAVY_EDGE)
    table.add_column("#", style="dim", width=2)
    table.add_column("Name")
    table.add_column("PID")
    table.add_column("Status")
    table.add_column("Runtime", justify="right")

    # todo: add rc
    pids = [
        1603,
        7646,
        5044,
    ]
    for index, pid in enumerate(pids, 1):
        p = psutil.Process(pid)
        runtime = time.time() - p.create_time()
        table.add_row(str(index), "name", str(pid), p.status(), humanize.naturaldelta(runtime))

    console.print(table)


if __name__ == '__main__':
    main()
