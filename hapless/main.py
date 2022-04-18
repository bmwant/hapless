import asyncio
import os
import shutil
import subprocess
import sys
import tempfile

try:
    from importlib.metadata import version
except ModuleNotFoundError:
    # Fallback for Python 3.7
    from importlib_metadata import version
from pathlib import Path
from typing import Dict, List, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from hapless import config
from hapless.hap import Hap
from hapless.utils import wait_created

"""
paused
running
finished
* finished(failed) non-zero rc
* finished(success) zero rc
💀
"""
console = Console(highlight=False)


class Hapless(object):
    def __init__(self):
        tmp_dir = Path(tempfile.gettempdir())
        self._hapless_dir = tmp_dir / "hapless"
        if not self._hapless_dir.exists():
            self._hapless_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def stats(haps: List[Hap]):
        if not haps:
            console.print(
                f"{config.ICON_INFO} No haps are currently running",
                style=f"{config.COLOR_MAIN} bold",
            )
            return

        package_version = version(__package__)
        table = Table(
            title=f"{config.ICON_HAP} {__package__}, {package_version}",
            show_header=True,
            header_style=f"{config.COLOR_MAIN} bold",
            box=box.HEAVY_EDGE,
        )
        table.add_column("#", style="dim", width=2)
        table.add_column("Name")
        table.add_column("PID")
        table.add_column("Status")
        table.add_column("RC")
        table.add_column("Runtime", justify="right")

        for hap in haps:
            table.add_row(
                f"{hap.hid}",
                hap.name,
                f"{hap.pid}",
                hap.status,
                f"{hap.rc}" if hap.rc is not None else "",
                hap.runtime,
            )

        console.print(table)

    @staticmethod
    def show(hap: Hap, verbose: bool = False):
        status_table = Table(show_header=False, show_footer=False, box=box.SIMPLE)

        status_table.add_row("Status:", hap.status)

        status_table.add_row("PID:", f"{hap.pid}")

        if hap.rc is not None:
            status_table.add_row("Return code:", f"{hap.rc}")

        cmd_text = Text(f"{hap.cmd}", style=f"{config.COLOR_ACCENT} bold")
        status_table.add_row("Command:", cmd_text)

        status_table.add_row("Runtime:", f"{hap.runtime}")

        status_panel = Panel(
            status_table,
            expand=verbose,
            title=f"Hap {config.ICON_HAP}{hap.hid}",
            subtitle=hap.name,
        )
        console.print(status_panel)

        if verbose:
            env_table = Table(show_header=False, show_footer=False, box=None)
            env_table.add_column("", justify="right")
            env_table.add_column("", justify="left", style=config.COLOR_ACCENT)
            environ = hap.env
            for key, value in environ.items():
                env_table.add_row(key, Text(value, overflow="fold"))

            env_panel = Panel(
                env_table,
                title="Environment",
                subtitle=f"{len(environ)} items",
                border_style=config.COLOR_MAIN,
            )
            console.print(env_panel)

    @property
    def dir(self) -> Path:
        return self._hapless_dir

    def _get_hap_dirs(self) -> List[str]:
        hap_dirs = filter(str.isdigit, os.listdir(self._hapless_dir))
        return sorted(hap_dirs, key=int)

    def _get_hap_names_map(self) -> Dict[str, str]:
        names = {}
        for dir in self._get_hap_dirs():
            filename = self._hapless_dir / dir / "name"
            if filename.exists():
                with open(filename) as f:
                    name = f.read().strip()
                    names[name] = dir
        return names

    def get_next_hap_id(self):
        dirs = self._get_hap_dirs()
        return 1 if not dirs else int(dirs[-1]) + 1

    def get_hap(self, hap_alias: str) -> Optional[Hap]:
        dirs = self._get_hap_dirs()
        # Check by hap id
        if hap_alias in dirs:
            return Hap(self._hapless_dir / hap_alias)

        # Check by hap name
        names_map = self._get_hap_names_map()
        if hap_alias in names_map:
            return Hap(self._hapless_dir / names_map[hap_alias])

    def get_haps(self) -> List[Hap]:
        haps = []
        if not self._hapless_dir.exists():
            return haps

        for dir in self._get_hap_dirs():
            hap_path = self._hapless_dir / dir
            haps.append(Hap(hap_path))
        return haps

    def create_hap(self, cmd: str, name: Optional[str] = None) -> Hap:
        hid = self.get_next_hap_id()
        hap_dir = self._hapless_dir / f"{hid}"
        hap_dir.mkdir()
        return Hap(hap_dir, cmd=cmd, name=name)

    async def run_hap(self, hap: Hap):
        with open(hap.stdout_path, "w") as stdout_pipe, open(
            hap.stderr_path, "w"
        ) as stderr_pipe:
            # todo: run with exec
            proc = await asyncio.create_subprocess_shell(
                hap.cmd,
                stdout=stdout_pipe,
                stderr=stderr_pipe,
            )
            hap.attach(proc.pid)

            console.print(f"{config.ICON_INFO} Running", hap)
            _ = await proc.communicate()

            with open(hap._rc_file, "w") as rc_file:
                rc_file.write(f"{proc.returncode}")

    def _check_fast_failure(self, hap: Hap):
        if wait_created(hap._rc_file) and hap.rc != 0:
            console.print(
                f"{config.ICON_INFO} Hap exited too quickly. stderr message:",
                style=f"{config.COLOR_ERROR} bold",
            )
            with open(hap.stderr_path) as f:
                console.print(f.read())
            sys.exit(1)

    def run(self, cmd: str, check: bool = False):
        hap = self.create_hap(cmd=cmd)
        pid = os.fork()
        if pid == 0:
            coro = self.run_hap(hap)
            asyncio.run(coro)
        else:
            if check:
                self._check_fast_failure(hap)
            sys.exit(0)

    def logs(self, hap: Hap, follow: bool = False):
        if follow:
            return subprocess.run(["tail", "-f", hap.stdout_path])
        else:
            return subprocess.run(["cat", hap.stdout_path])

    def clean(self, skip_failed: bool = False):
        def to_clean(hap):
            if hap.rc is not None:
                return hap.rc == 0 or not skip_failed
            return False

        haps = list(filter(to_clean, self.get_haps()))
        for hap in haps:
            shutil.rmtree(hap.path)

        if haps:
            console.print(
                f"{config.ICON_INFO} Deleted {len(haps)} finished haps",
                style=f"{config.COLOR_MAIN} bold",
            )
        else:
            console.print(
                f"{config.ICON_INFO} Nothing to clean",
                style=f"{config.COLOR_ERROR} bold",
            )
