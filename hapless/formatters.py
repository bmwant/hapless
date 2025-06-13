try:
    from importlib.metadata import version
except ModuleNotFoundError:
    # Fallback for Python 3.7
    from importlib_metadata import version

import abc
import json
from itertools import filterfalse
from typing import List

from rich import box
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from hapless import config
from hapless.hap import Hap, Status


class Formatter(abc.ABC):
    """
    Abstract base class for formatting Hap objects.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    @abc.abstractmethod
    def format_one(self, hap: Hap) -> RenderableType:
        pass

    @abc.abstractmethod
    def format_list(self, haps: List[Hap]) -> RenderableType:
        pass


class TableFormatter(Formatter):
    """
    Formats Hap objects as a rich table.
    """

    def _get_status_text(self, status: Status) -> Text:
        color = config.STATUS_COLORS.get(status)
        status_text = Text()
        status_text.append(config.ICON_STATUS, style=color)
        status_text.append(f" {status.value}")
        return status_text

    def format_one(self, hap: Hap) -> Group:
        status_table = Table(show_header=False, show_footer=False, box=box.SIMPLE)

        status_text = self._get_status_text(hap.status)
        status_table.add_row("Status:", status_text)

        status_table.add_row("PID:", f"{hap.pid or '-'}")

        if hap.rc is not None:
            status_table.add_row("Return code:", f"{hap.rc}")

        cmd_text = Text(f"{hap.cmd}", style=f"{config.COLOR_ACCENT} bold")
        status_table.add_row("Command:", cmd_text)

        proc = hap.proc
        if self.verbose and proc is not None:
            status_table.add_row("Working dir:", f"{proc.cwd()}")
            status_table.add_row("Parent PID:", f"{proc.ppid()}")
            status_table.add_row("User:", f"{proc.username()}")

        if self.verbose:
            status_table.add_row("Stdout file:", f"{hap.stdout_path}")
            status_table.add_row("Stderr file:", f"{hap.stderr_path}")

        start_time = hap.start_time
        end_time = hap.end_time
        if self.verbose and start_time:
            status_table.add_row("Start time:", f"{start_time}")

        if self.verbose and end_time:
            status_table.add_row("End time:", f"{end_time}")

        status_table.add_row("Runtime:", f"{hap.runtime}")

        status_panel = Panel(
            status_table,
            expand=self.verbose,
            title=f"Hap {config.ICON_HAP}{hap.hid}",
            subtitle=hap.name,
        )
        result = Group(status_panel)

        environ = hap.env
        if self.verbose and environ is not None:
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
            result = Group(status_panel, env_panel)
        return result

    def format_list(self, haps: List[Hap]) -> Table:
        package_version = version(__package__)
        table = Table(
            show_header=True,
            header_style=f"{config.COLOR_MAIN} bold",
            box=box.HEAVY_EDGE,
            caption_style="dim",
            caption_justify="right",
        )
        table.add_column("#", style="dim", min_width=2)
        table.add_column("Name")
        table.add_column("PID")
        if self.verbose:
            table.add_column("Command")
            table.add_column("Owner")
        table.add_column("Status")
        table.add_column("RC", justify="right")
        table.add_column("Runtime", justify="right")

        active_haps = 0
        for hap in haps:
            active_haps += 1 if hap.active else 0
            name = Text(hap.name)
            if hap.restarts:
                name += Text(f"{config.RESTART_DELIM}{hap.restarts}", style="dim")
            pid_text = (
                f"{hap.pid}" if hap.active else Text(f"{hap.pid or '-'}", style="dim")
            )
            command_text = Text(
                hap.cmd, overflow="ellipsis", style=f"{config.COLOR_ACCENT}"
            )
            status_text = self._get_status_text(hap.status)
            command_text.truncate(config.TRUNCATE_LENGTH)
            row = [
                f"{hap.hid}",
                name,
                pid_text,
                command_text if self.verbose else None,
                hap.owner if self.verbose else None,
                status_text,
                f"{hap.rc}" if hap.rc is not None else "",
                hap.runtime,
            ]
            table.add_row(*filterfalse(lambda x: x is None, row))

        if self.verbose:
            table.title = f"{config.ICON_HAP} {__package__}, {package_version}"
            table.caption = f"{active_haps} active / {len(haps)} total"

        return table


class JSONFormatter(Formatter):
    """
    Formats Hap objects as a valid JSON.
    """

    def format_one(self, hap: Hap) -> str:
        return json.dumps(hap.serialize())

    def format_list(self, haps: List[Hap]) -> str:
        return json.dumps([hap.serialize() for hap in haps])
