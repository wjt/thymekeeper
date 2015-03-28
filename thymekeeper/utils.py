import contextlib
import time

from datetime import datetime


def isodate(s):
    return datetime.strptime(s, '%Y-%m-%d').date()

def isomonth(s):
    return datetime.strptime(s, '%Y-%m').date()

@contextlib.contextmanager
def stopwatch(log, message, *args):
    m = message % args if args else message
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        log.debug("%s took %fs", m, t1 - t0)
