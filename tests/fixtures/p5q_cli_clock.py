"""Production CLI entry under a test-only polling clock; I/O and driver clocks stay real."""

import runpy
from types import SimpleNamespace

from ci_triage import qb_discovery, qb_trigger

now = 0.0


def sleep(seconds):
    global now
    now += seconds


clock = SimpleNamespace(monotonic=lambda: now, sleep=sleep)
qb_discovery.time = clock
qb_trigger.time = clock
runpy.run_module("ci_triage", run_name="__main__")
