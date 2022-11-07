import asyncio
import os
import shutil
import signal
import subprocess
import sys
import tempfile

try:
    from importlib.metadata import version
except ModuleNotFoundError:
    # Fallback for Python 3.7
    from importlib_metadata import version

from itertools import filterfalse
from pathlib import Path
from typing import Dict, List, Optional

import psutil
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from hapless import config
from hapless.hap import Hap
from hapless.utils import logger, wait_created

console = Console(highlight=False)


class Hapless(object):
    def __init__(self, hapless_dir: Path = None):
        default_dir = Path(tempfile.gettempdir()) / "hapless"
        self._hapless_dir = hapless_dir or default_dir
        logger.debug(f"Initialized within {self._hapless_dir} dir")
        if not self._hapless_dir.exists():
            self._hapless_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def stats(haps: List[Hap], verbose: bool = False):
        if not haps:
            console.print(
                f"{config.ICON_INFO} No haps are currently running",
                style=f"{config.COLOR_MAIN} bold",
            )
            return

        package_version = version(__package__)
        table = Table(
            show_header=True,
            header_style=f"{config.COLOR_MAIN} bold",
            box=box.HEAVY_EDGE,
            caption_style="dim",
            caption_justify="right",
        )
        table.add_column("#", style="dim", width=2)
        table.add_column("Name")
        table.add_column("PID")
        if verbose:
            table.add_column("Command")
        table.add_column("Status")
        table.add_column("RC", justify="right")
        table.add_column("Runtime", justify="right")

        active_haps = 0
        for hap in haps:
            active_haps += 1 if hap.active else 0
            pid_text = f"{hap.pid}" if hap.active else Text(f"{hap.pid}", style="dim")
            command_text = Text(
                hap.cmd, overflow="ellipsis", style=f"{config.COLOR_ACCENT}"
            )
            status_text = Hapless._get_status_text(hap.status)
            command_text.truncate(config.TRUNCATE_LENGTH)
            row = [
                f"{hap.hid}",
                hap.name,
                pid_text,
                command_text if verbose else None,
                status_text,
                f"{hap.rc}" if hap.rc is not None else "",
                hap.runtime,
            ]
            table.add_row(*filterfalse(lambda x: x is None, row))

        if verbose:
            table.title = f"{config.ICON_HAP} {__package__}, {package_version}"
            table.caption = f"{active_haps} active / {len(haps)} total"
        console.print(table)

    @staticmethod
    def _get_status_text(status) -> Text:
        color = config.STATUS_COLORS.get(status)
        status_text = Text()
        status_text.append(config.ICON_STATUS, style=color)
        status_text.append(f" {status}")
        return status_text

    @staticmethod
    def show(hap: Hap, verbose: bool = False):
        status_table = Table(show_header=False, show_footer=False, box=box.SIMPLE)

        status_table.add_row("Status:", hap.status)

        status_table.add_row("PID:", f"{hap.pid}")

        if hap.rc is not None:
            status_table.add_row("Return code:", f"{hap.rc}")

        cmd_text = Text(f"{hap.cmd}", style=f"{config.COLOR_ACCENT} bold")
        status_table.add_row("Command:", cmd_text)

        proc = hap.proc
        if verbose and proc is not None:
            status_table.add_row("Working dir:", f"{proc.cwd()}")
            status_table.add_row("Parent PID:", f"{proc.ppid()}")
            status_table.add_row("User:", f"{proc.username()}")

        if verbose:
            status_table.add_row("Stdout file:", f"{hap.stdout_path}")
            status_table.add_row("Stderr file:", f"{hap.stderr_path}")

        start_time = hap.start_time
        end_time = hap.end_time
        if verbose and start_time:
            status_table.add_row("Start time:", f"{start_time}")

        if verbose and end_time:
            status_table.add_row("End time:", f"{end_time}")

        status_table.add_row("Runtime:", f"{hap.runtime}")

        status_panel = Panel(
            status_table,
            expand=verbose,
            title=f"Hap {config.ICON_HAP}{hap.hid}",
            subtitle=hap.name,
        )
        console.print(status_panel)

        environ = hap.env
        if verbose and environ is not None:
            env_table = Table(show_header=False, show_footer=False, box=None)
            env_table.add_column("", justify="right")
            env_table.add_column("", justify="left", style=config.COLOR_ACCENT)

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

    def pause_hap(self, hap: Hap):
        proc = hap.proc
        if proc is not None:
            proc.suspend()
            console.print(f"{config.ICON_INFO} Paused", hap)
        else:
            console.print(
                f"{config.ICON_INFO} Cannot pause. Hap {hap} is not running",
                style=f"{config.COLOR_ERROR} bold",
            )
            sys.exit(1)

    def resume_hap(self, hap: Hap):
        proc = hap.proc
        if proc is not None and proc.status() == psutil.STATUS_STOPPED:
            proc.resume()
            console.print(f"{config.ICON_INFO} Resumed", hap)
        else:
            console.print(
                f"{config.ICON_INFO} Cannot resume. Hap {hap} is not suspended",
                style=f"{config.COLOR_ERROR} bold",
            )
            sys.exit(1)

    def run(self, cmd: str, name: Optional[str] = None, check: bool = False):
        hap = self.create_hap(cmd=cmd, name=name)
        pid = os.fork()
        if pid == 0:
            coro = self.run_hap(hap)
            asyncio.run(coro)
        else:
            if check:
                self._check_fast_failure(hap)
            sys.exit(0)

    def logs(self, hap: Hap, stderr: bool = False, follow: bool = False):
        filepath = hap.stderr_path if stderr else hap.stdout_path
        if follow:
            console.print(
                f"{config.ICON_INFO} Streaming {filepath} file...",
                style=f"{config.COLOR_MAIN} bold",
            )
            return subprocess.run(["tail", "-f", filepath])
        else:
            return subprocess.run(["cat", filepath])

    def clean(self, skip_failed: bool = False):
        def to_clean(hap):
            if hap.rc is not None:
                return hap.rc == 0 or not skip_failed
            return False

        haps = list(filter(to_clean, self.get_haps()))
        for hap in haps:
            logger.debug(f"Removing {hap.path}")
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

    def kill(self, haps: List[Hap]):
        killed_counter = 0
        for hap in haps:
            if hap.active:
                logger.info(f"Killing {hap}...")
                hap.proc.kill()
                killed_counter += 1

        if killed_counter:
            console.print(
                f"{config.ICON_KILLED} Killed {killed_counter} active haps",
                style=f"{config.COLOR_MAIN} bold",
            )
        else:
            console.print(
                f"{config.ICON_INFO} No active haps to kill",
                style=f"{config.COLOR_ERROR} bold",
            )

    def signal(self, hap: Hap, sig: signal.Signals):
        if hap.active:
            sig_text = (
                f"[bold]{sig.name}[/] ([{config.COLOR_MAIN}]{signal.strsignal(sig)}[/])"
            )
            console.print(f"{config.ICON_INFO} Sending {sig_text} to hap {hap}")
            hap.proc.send_signal(sig)
        else:
            console.print(
                f"{config.ICON_INFO} Cannot send signal to the inactive hap",
                style=f"{config.COLOR_ERROR} bold",
            )
