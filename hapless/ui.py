from typing import List, Optional

from rich.console import Console
from rich.live import Live

from hapless import config
from hapless.formatters import Formatter, TableFormatter
from hapless.hap import Hap


class ConsoleUI:
    def __init__(self, disable: bool = False) -> None:
        self.console = Console(highlight=False, quiet=disable)
        self.default_formatter = TableFormatter()
        self.disable = disable

    def print(self, *args, **kwargs):
        return self.console.print(*args, **kwargs)

    def print_plain(self, text: str):
        return self.console.print(
            text,
            markup=False,
            highlight=False,
            emoji=False,
            no_wrap=True,
            overflow="ignore",
            crop=False,
        )

    def error(self, message: str):
        return self.console.print(
            f"{config.ICON_INFO} {message}",
            style=f"{config.COLOR_ERROR} bold",
            overflow="ignore",
            crop=False,
        )

    def get_live(self):
        return Live(
            console=self.console,
            refresh_per_second=10,
            transient=True,
        )

    def stats(self, haps: List[Hap], formatter: Optional[Formatter] = None):
        if not haps:
            self.console.print(
                f"{config.ICON_INFO} No haps are currently running",
                style=f"{config.COLOR_MAIN} bold",
            )
            return
        formatter = formatter or self.default_formatter
        haps_data = formatter.format_list(haps)
        self.console.print(haps_data, soft_wrap=True)

    def show_one(self, hap: Hap, formatter: Optional[Formatter] = None):
        formatter = formatter or self.default_formatter
        hap_data = formatter.format_one(hap)
        self.console.print(hap_data, soft_wrap=True)
