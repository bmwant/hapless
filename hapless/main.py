import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import psutil

from hapless import config
from hapless.hap import Hap, Status
from hapless.ui import ConsoleUI
from hapless.utils import kill_proc_tree, logger, wait_created


class Hapless(object):
    def __init__(self, hapless_dir: Optional[Path] = None):
        default_dir = Path(tempfile.gettempdir()) / "hapless"
        self._hapless_dir = hapless_dir or default_dir
        logger.debug(f"Initialized within {self._hapless_dir} dir")
        if not self._hapless_dir.exists():
            self._hapless_dir.mkdir(parents=True, exist_ok=True)
        self.ui = ConsoleUI()

    def stats(self, haps: List[Hap], verbose: bool = False):
        self.ui.stats(haps, verbose=verbose)

    def show(self, hap: Hap, verbose: bool = False):
        self.ui.show_one(hap, verbose=verbose)

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

    def _get_next_hap_id(self) -> int:
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

    def create_hap(
        self, cmd: str, name: Optional[str] = None, restarts: int = 0
    ) -> Hap:
        hid = self._get_next_hap_id()
        hap_dir = self._hapless_dir / f"{hid}"
        hap_dir.mkdir()
        return Hap(hap_dir, cmd=cmd, name=name, restarts=restarts)

    def run_hap(self, hap: Hap):
        with open(hap.stdout_path, "w") as stdout_pipe, open(
            hap.stderr_path, "w"
        ) as stderr_pipe:
            self.ui.print(f"{config.ICON_INFO} Launching", hap)
            shell_exec = os.getenv("SHELL")
            if shell_exec is not None:
                logger.debug(f"Using {shell_exec} to run hap")
            proc = subprocess.Popen(
                hap.cmd,
                shell=True,
                executable=shell_exec,
                stdout=stdout_pipe,
                stderr=stderr_pipe,
            )

            pid = proc.pid
            logger.debug(f"Attaching hap {hap} to pid {pid}")
            hap.bind(pid)

            retcode = proc.wait()

            with open(hap._rc_file, "w") as rc_file:
                rc_file.write(f"{retcode}")

    def _check_fast_failure(self, hap: Hap):
        if wait_created(hap._rc_file) and hap.rc != 0:
            self.ui.print(
                f"{config.ICON_INFO} Hap exited too quickly. stderr message:",
                style=f"{config.COLOR_ERROR} bold",
            )
            with open(hap.stderr_path) as f:
                self.ui.print(f.read())
            sys.exit(1)

    def pause_hap(self, hap: Hap):
        proc = hap.proc
        if proc is not None:
            proc.suspend()
            self.ui.print(f"{config.ICON_INFO} Paused", hap)
        else:
            self.ui.print(
                f"{config.ICON_INFO} Cannot pause. Hap {hap} is not running",
                style=f"{config.COLOR_ERROR} bold",
            )
            sys.exit(1)

    def resume_hap(self, hap: Hap):
        proc = hap.proc
        if proc is not None and proc.status() == psutil.STATUS_STOPPED:
            proc.resume()
            self.ui.print(f"{config.ICON_INFO} Resumed", hap)
        else:
            self.ui.print(
                f"{config.ICON_INFO} Cannot resume. Hap {hap} is not suspended",
                style=f"{config.COLOR_ERROR} bold",
            )
            sys.exit(1)

    def run(
        self,
        cmd: str,
        name: Optional[str] = None,
        check: bool = False,
        restarts: int = 0,
    ):
        hap = self.create_hap(cmd=cmd, name=name, restarts=restarts)
        pid = os.fork()
        if pid == 0:
            self.run_hap(hap)
        else:
            if check:
                self._check_fast_failure(hap)
            sys.exit(0)

    def logs(self, hap: Hap, stderr: bool = False, follow: bool = False):
        filepath = hap.stderr_path if stderr else hap.stdout_path
        if follow:
            self.ui.print(
                f"{config.ICON_INFO} Streaming {filepath} file...",
                style=f"{config.COLOR_MAIN} bold",
            )
            return subprocess.run(["tail", "-f", filepath])
        else:
            return subprocess.run(["cat", filepath])

    def _clean_haps(self, filter_haps) -> int:
        haps = list(filter(filter_haps, self.get_haps()))
        for hap in haps:
            logger.debug(f"Removing {hap.path}")
            shutil.rmtree(hap.path)
        return len(haps)

    def _clean_one(self, hap: Hap):
        def to_clean(hap_arg: Hap) -> bool:
            return hap_arg.hid == hap.hid

        haps_count = self._clean_haps(filter_haps=to_clean)
        logger.debug(f"Deleted {haps_count} haps")

    def clean(self, clean_all: bool = False):
        def to_clean(hap: Hap) -> bool:
            return hap.status == Status.SUCCESS or (
                hap.status == Status.FAILED and clean_all
            )

        haps_count = self._clean_haps(filter_haps=to_clean)

        if haps_count:
            self.ui.print(
                f"{config.ICON_INFO} Deleted {haps_count} finished haps",
                style=f"{config.COLOR_MAIN} bold",
            )
        else:
            self.ui.print(
                f"{config.ICON_INFO} Nothing to clean",
                style=f"{config.COLOR_ERROR} bold",
            )

    def kill(self, haps: List[Hap], verbose: bool = True):
        killed_counter = 0
        for hap in haps:
            if hap.active:
                logger.info(f"Killing {hap}...")
                kill_proc_tree(hap.pid)
                killed_counter += 1

        if killed_counter and verbose:
            self.ui.print(
                f"{config.ICON_KILLED} Killed {killed_counter} active haps",
                style=f"{config.COLOR_MAIN} bold",
            )
        elif verbose:
            self.ui.print(
                f"{config.ICON_INFO} No active haps to kill",
                style=f"{config.COLOR_ERROR} bold",
            )

    def signal(self, hap: Hap, sig: signal.Signals):
        if hap.active:
            sig_text = (
                f"[bold]{sig.name}[/] ([{config.COLOR_MAIN}]{signal.strsignal(sig)}[/])"
            )
            self.ui.print(f"{config.ICON_INFO} Sending {sig_text} to hap {hap}")
            hap.proc.send_signal(sig)
        else:
            self.ui.print(
                f"{config.ICON_INFO} Cannot send signal to the inactive hap",
                style=f"{config.COLOR_ERROR} bold",
            )

    def restart(self, hap: Hap):
        hid, name, cmd, restarts = hap.hid, hap.name, hap.cmd, hap.restarts

        if hap.active:
            self.kill([hap], verbose=False)

        hap_killed = self.get_hap(hid)
        while hap_killed.active:
            hap_killed = self.get_hap(hid)

        self._clean_one(hap_killed)

        self.run(cmd=cmd, name=name, restarts=restarts + 1)
