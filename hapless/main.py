import getpass
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

import psutil

from hapless import config
from hapless.formatters import Formatter
from hapless.hap import Hap, Status
from hapless.ui import ConsoleUI
from hapless.utils import kill_proc_tree, logger, wait_created


class Hapless:
    def __init__(
        self,
        hapless_dir: Optional[Union[Path, str]] = None,
        *,
        quiet: bool = False,
    ):
        self.ui = ConsoleUI(disable=quiet)
        user = getpass.getuser()
        default_dir = Path(tempfile.gettempdir()) / "hapless"

        hapless_dir = Path(hapless_dir or default_dir)
        try:
            if not hapless_dir.exists():
                hapless_dir.mkdir(parents=True, exist_ok=True)
            os.utime(hapless_dir)
        except PermissionError as e:
            logger.error(f"Cannot initialize state directory {hapless_dir}: {e}")
            self.ui.error(
                f"State directory {hapless_dir} is not accessible by user {user}"
            )
            sys.exit(1)

        self._hapless_dir = hapless_dir
        logger.debug(f"Initialized within {self._hapless_dir} dir")

    def stats(self, haps: List[Hap], formatter: Formatter):
        self.ui.stats(haps, formatter=formatter)

    def show(self, hap: Hap, formatter: Formatter):
        self.ui.show_one(hap, formatter=formatter)

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
                    raw_name = f.read().strip()
                    name = raw_name.split(config.RESTART_DELIM)[0]
                    names[name] = dir
        return names

    def _get_next_hap_id(self) -> str:
        dirs = self._get_hap_dirs()
        next_num = 1 if not dirs else int(dirs[-1]) + 1
        return f"{next_num}"

    def get_hap(self, hap_alias: str) -> Optional[Hap]:
        dirs = self._get_hap_dirs()
        # Check by hap id
        if hap_alias in dirs:
            return Hap(self._hapless_dir / hap_alias)

        # Check by hap name
        names_map = self._get_hap_names_map()
        if hap_alias in names_map:
            return Hap(self._hapless_dir / names_map[hap_alias])

    def _get_all_haps(self) -> List[Hap]:
        """
        Get all haps available in the hapless state directory.
        Current user might only be able to access subset of them.
        """
        haps = []
        if not self._hapless_dir.exists():
            return haps

        for dir in self._get_hap_dirs():
            hap_path = self._hapless_dir / dir
            haps.append(Hap(hap_path))
        return haps

    def get_haps(self, accessible_only=True) -> List[Hap]:
        """
        Get all haps that are managable by the current user.
        If `accessible_only` is set to False, all haps will be returned.
        """

        def filter_haps(hap_arg: Hap) -> bool:
            return hap_arg.accessible if accessible_only else True

        haps = list(filter(filter_haps, self._get_all_haps()))
        return haps

    def create_hap(
        self,
        cmd: str,
        workdir: Optional[Union[str, Path]] = None,
        hid: Optional[str] = None,
        name: Optional[str] = None,
        *,
        redirect_stderr: Optional[bool] = None,
    ) -> Hap:
        hid = hid or self._get_next_hap_id()
        hap_dir = self._hapless_dir / f"{hid}"
        hap_dir.mkdir()
        if redirect_stderr is None:
            redirect_stderr = config.REDIRECT_STDERR
        if workdir is None or not Path(workdir).exists():
            workdir = os.getcwd()
        return Hap(
            hap_dir,
            name=name,
            cmd=cmd,
            workdir=workdir,
            redirect_stderr=redirect_stderr,
        )

    def _wrap_subprocess(self, hap: Hap):
        try:
            stdout_pipe = open(hap.stdout_path, "w")
            stderr_pipe = stdout_pipe
            if not hap.redirect_stderr:
                stderr_pipe = open(hap.stderr_path, "w")
            shell_exec = os.getenv("SHELL")
            if shell_exec is not None:
                logger.debug(f"Using {shell_exec} to run hap")
            proc = subprocess.Popen(
                hap.cmd,
                cwd=hap.workdir,
                shell=True,
                executable=shell_exec,
                stdout=stdout_pipe,
                stderr=stderr_pipe,
            )

            pid = proc.pid
            logger.debug(f"Attaching hap {hap} to pid {pid}")
            hap.bind(pid)

            retcode = proc.wait()
        finally:
            stdout_pipe.close()
            stderr_pipe.close()

        hap.set_return_code(retcode)

    def _check_fast_failure(self, hap: Hap) -> None:
        timeout = config.FAILFAST_TIMEOUT
        wait_created(
            hap._rc_file,
            live_context=self.ui.get_live(),
            interval=0.5,
            timeout=timeout,
        )
        return_code: Optional[int] = hap.rc
        if return_code is None:
            # no return code yet, process is still running
            self.ui.print(
                f"{config.ICON_INFO} Hap is healthy "
                f"and still running after {timeout} seconds",
                style=f"{config.COLOR_ACCENT} bold",
            )
        elif return_code == 0:
            # finished quickly, but successfully
            self.ui.print(
                f"{config.ICON_INFO} Hap finished successfully "
                f"in less than {timeout} seconds",
                style=f"{config.COLOR_ACCENT} bold",
            )
        else:
            # non-zero return code
            self.ui.error("Hap exited too quickly. stderr message:")
            self.ui.print(hap.stderr_path.read_text())
            sys.exit(1)

    def run_hap(
        self,
        hap: Hap,
        check: bool = False,
        *,
        blocking: bool = False,
    ) -> None:
        """
        Run hap in a separate process.
        If `check` is True, it will check for fast failure and exit
        if hap terminates too quickly.
        """
        if blocking:
            # NOTE: this is for the testing purposes only
            self._wrap_subprocess(hap)
            return

        self.ui.print(f"{config.ICON_INFO} Launching", hap)
        # TODO: or sys.platform == "win32"
        if config.NO_FORK:
            logger.debug("Forking is disabled, running using spawn via wrapper")
            self._run_via_spawn(hap)
        else:
            logger.debug("Running hap using fork")
            self._run_via_fork(hap)

        logger.debug(f"Parent process continues with pid {os.getpid()}")
        if check:
            self._check_fast_failure(hap)

    def _run_via_spawn(self, hap: Hap) -> None:
        exec_path = shutil.which("hapwrap")
        if exec_path is None:
            self.ui.error(
                "Cannot find wrapper to run process. Please reinstall hapless"
            )
            sys.exit(1)

        proc = subprocess.Popen(
            [f"{exec_path}", f"{hap.hid}"],
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.debug(f"Running subprocess in child with pid {proc.pid}")
        logger.debug(f"Using wrapper located at {exec_path}")

    def _run_via_fork(self, hap: Hap) -> None:
        pid = os.fork()
        if pid == 0:
            os.setsid()
            logger.debug(f"Running subprocess in child with pid {os.getpid()}")
            self._wrap_subprocess(hap)
            # NOTE: to prevent deadlocks in multi-threaded environments
            # https://docs.python.org/3/library/os.html#os._exit
            os._exit(0)

    def run_command(
        self,
        cmd: str,
        workdir: Optional[Union[str, Path]] = None,
        hid: Optional[str] = None,
        name: Optional[str] = None,
        check: bool = False,
        *,
        redirect_stderr: Optional[bool] = None,
        blocking: bool = False,
    ) -> None:
        """
        For the command provided create a hap and run it.
        If `hid` or `name` is not provided, it will be generated automatically.
        """
        hap = self.create_hap(
            cmd=cmd,
            workdir=workdir,
            hid=hid,
            name=name,
            redirect_stderr=redirect_stderr,
        )
        self.run_hap(hap, check=check, blocking=blocking)

    def pause_hap(self, hap: Hap):
        proc = hap.proc
        if proc is not None:
            proc.suspend()
            self.ui.print(f"{config.ICON_INFO} Paused", hap)
        else:
            self.ui.error(f"Cannot pause. Hap {hap} is not running")
            sys.exit(1)

    def resume_hap(self, hap: Hap):
        proc = hap.proc
        if proc is not None and proc.status() == psutil.STATUS_STOPPED:
            proc.resume()
            self.ui.print(f"{config.ICON_INFO} Resumed", hap)
        else:
            self.ui.error(f"Cannot resume. Hap {hap} is not suspended")
            sys.exit(1)

    def logs(self, hap: Hap, stderr: bool = False, follow: bool = False):
        filepath = hap.stderr_path if stderr else hap.stdout_path
        if follow:
            self.ui.print(
                f"{config.ICON_INFO} Streaming {filepath} file...",
                style=f"{config.COLOR_MAIN} bold",
            )
            return subprocess.run(["tail", "-f", filepath])

        text = filepath.read_text()
        if not text:
            self.ui.error("No logs found")
            return

        self.ui.print(
            f"{config.ICON_INFO} Showing logs at {filepath}",
            style=f"{config.COLOR_MAIN} bold",
        )
        self.ui.print_plain(text)

    def _clean_haps(self, filter_haps) -> int:
        haps = list(filter(filter_haps, self.get_haps()))
        for hap in haps:
            logger.debug(f"Removing {hap.path}")
            shutil.rmtree(hap.path, ignore_errors=True)
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
            self.ui.error("Nothing to clean")

    def kill(self, haps: List[Hap], verbose: bool = True) -> int:
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
            self.ui.error("No active haps to kill")
        return killed_counter

    def signal(self, hap: Hap, sig: signal.Signals):
        if hap.active:
            sig_text = (
                f"[bold]{sig.name}[/] ([{config.COLOR_MAIN}]{signal.strsignal(sig)}[/])"
            )
            self.ui.print(f"{config.ICON_INFO} Sending {sig_text} to hap {hap}")
            hap.proc.send_signal(sig)
        else:
            self.ui.error("Cannot send signal to the inactive hap")

    def restart(self, hap: Hap) -> None:
        hid, name, cmd, workdir, restarts, redirect_stderr = (
            hap.hid,
            hap.name,
            hap.cmd,
            hap.workdir,
            hap.restarts,
            hap.redirect_stderr,
        )
        if hap.active:
            self.kill([hap], verbose=False)

        hap_killed = self.get_hap(hid)
        while hap_killed.active:
            # NOTE: re-read is required as `proc` is a cached property
            hap_killed = self.get_hap(hid)

        rc_exists = wait_created(hap_killed._rc_file, timeout=1)
        if not rc_exists:
            logger.error(
                f"Hap {hap_killed} process was killed, "
                f"but parent did not write return code"
            )

        self._clean_one(hap_killed)

        name = f"{name}{config.RESTART_DELIM}{restarts + 1}"
        self.run_command(
            cmd=cmd,
            workdir=workdir,
            hid=hid,
            name=name,
            redirect_stderr=redirect_stderr,
        )

    def rename_hap(self, hap: Hap, new_name: str):
        rich_text = (
            f"{config.ICON_INFO} Renamed [{config.COLOR_ACCENT}]{hap.name}[/] "
            f"to [{config.COLOR_MAIN} bold]{new_name}[/]"
        )
        if hap.restarts:
            new_name = f"{new_name}{config.RESTART_DELIM}{hap.restarts}"
        hap.set_name(new_name)
        self.ui.print(rich_text)
