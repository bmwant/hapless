import os

DEBUG = bool(os.getenv("HAPLESS_DEBUG", default=""))
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
