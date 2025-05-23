from rich.console import Console

from hapless import config


class ConsoleUI:
    def __init__(self):
        self.console = Console(highlight=False)

    def print(self, *args, **kwargs):
        return self.console.print(*args, **kwargs)

    def error(self, message: str):
        return self.console.print(
            f"{config.ICON_INFO} {message}",
            style=f"{config.COLOR_ERROR} bold",
            overflow="ignore",
            crop=False,
        )

    def stats(self, formatted_output: str):
        self.console.print(formatted_output)

    def show_one(self, formatted_output: str):
        self.console.print(formatted_output)
