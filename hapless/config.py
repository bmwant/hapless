import os

DEBUG = bool(os.getenv("HAPLESS_DEBUG", default=""))
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

COLOR_HEADER = ""
COLOR_ACCENT = "#3aaed8"
ICON_HAP = "⚡️"
ICON_SUCCESS = ""
ICON_FAILED = ""
