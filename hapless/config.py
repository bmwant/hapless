import os

DEBUG = bool(os.getenv("HAPLESS_DEBUG", default=""))
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

COLOR_HEADER = "#fdca40"
"""
f4a259
"""
COLOR_ACCENT = "#3aaed8"
COLOR_ERROR = "#f64740"

ICON_HAP = "⚡️"
ICON_INFO = "🧲"
ICON_SUCCESS = "🟢"
ICON_RUNNING = "🟠"
ICON_PAUSED = "⚪️"
ICON_FAILED = "🔴"
