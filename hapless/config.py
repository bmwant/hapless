from pathlib import Path
from typing import Optional

import environ

env = environ.Env()

DEBUG = env.bool("HAPLESS_DEBUG", default=False)

HAPLESS_DIR: Optional[Path] = env("HAPLESS_DIR", cast=Path, default=None)

COLOR_MAIN = "#fdca40"
COLOR_ACCENT = "#3aaed8"
COLOR_ERROR = "#f64740"
STATUS_COLORS = {
    "running": "#f79824",
    "paused": "#f6efee",
    "success": "#4aad52",
    "failed": COLOR_ERROR,
}

ICON_HAP = "⚡️"
ICON_INFO = "🧲"
ICON_STATUS = "•"
ICON_KILLED = "💀"

FAILFAST_TIMEOUT = env.int("HAPLESS_FAILFAST_TIMEOUT", default=5)
DATETIME_FORMAT = "%H:%M:%S %Y/%m/%d"
TRUNCATE_LENGTH = 36
RESTART_DELIM = "@"

NO_FORK = env.bool("HAPLESS_NO_FORK", default=False)

REDIRECT_STDERR = env.bool("HAPLESS_REDIRECT_STDERR", default=False)
