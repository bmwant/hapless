import os

DEBUG = bool(os.getenv("HAPLESS_DEBUG", default=""))
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

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

FAILFAST_DELAY = 2
DATETIME_FORMAT = "%H:%M:%S %Y/%m/%d"
TRUNCATE_LENGTH = 36
