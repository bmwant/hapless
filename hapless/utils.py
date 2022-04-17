import time
from functools import wraps


def allow_missing(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            pass

    return wrapper


class timed(object):
    def __init__(self):
        self._start = time.time()
        self._end = None

    @property
    def elapsed(self):
        if self._end is not None:
            return self._end - self._start

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._end = time.time()
        return self


def wait_created(path, interval=0.1, timeout=2):
    start = time.time()
    while not path.exists() and time.time() - start < timeout:
        time.sleep(interval)
    return path.exists()
