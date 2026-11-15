"""DEVELOPMENT ONLY: a deterministic virtual CPU clock for paired synthesis experiments.

The synthesisers stop on `time.process_time()` deadlines, so two runs of the same arm on the same input can take
different paths when the machine is busier (observed: the same 5 s first-fit synthesis fits or fails between runs).
For a causal A/B/C comparison that noise must not be counted as an effect.  This shim replaces the module-level
`time` of the synthesis modules by a clock that advances only with work the code does:

    virtual seconds = WORK_QUANTUM * invention_core.WORK + CALL_QUANTUM * (clock reads)

`invention_core.WORK` counts primitive evaluations; clock reads are made in every search loop.  Both are
deterministic for fixed inputs and PYTHONHASHSEED, so a run is reproducible bit for bit and every arm gets the same
budget in the same unit.  The quanta are calibrated once against real CPU seconds on the development machine
(`calibrate`); the unit is disclosed with every result.  Nothing in `neumann1/` imports this module and the default
solver still uses the real clock.
"""
from __future__ import annotations
import time as _real

from neumann1 import invention_core as ic

MODULES = ("neumann1.latent", "neumann1.relcells", "neumann1.cells", "neumann1.discovery_core",
           "neumann1.invention_core", "neumann1.spec_core", "neumann1.active", "neumann1.opgen", "neumann1.inverted")
# calibrated on the development container (30 first-fit synthesis calls on the 10 list snapshots, real CPU
# seconds = a*WORK + b*reads by least squares: a = 2.92e-7, b = 5.20e-5; rounded)
WORK_QUANTUM = 3.0e-7
CALL_QUANTUM = 5.0e-5


class VirtualTime:
    def __init__(self, wq=None, cq=None, real=False):
        self.wq = WORK_QUANTUM if wq is None else wq
        self.cq = CALL_QUANTUM if cq is None else cq
        self.real = real            # calibration mode: real CPU clock, reads still counted
        self.calls = 0

    def process_time(self):
        self.calls += 1
        if self.real:
            return _real.process_time()
        return ic.WORK[0] * self.wq + self.calls * self.cq

    perf_counter = process_time

    def time(self):
        return _real.time()

    def sleep(self, s):
        return _real.sleep(s)

    def __getattr__(self, name):
        return getattr(_real, name)


_SAVED = {}


def install(clock, extra=()):
    """Every synthesis module AND the calling harness modules (`extra`: module objects that compute deadlines
    with `time.process_time()`) must read the same clock, or deadlines mix units."""
    import importlib
    mods = [importlib.import_module(name) for name in MODULES] + list(extra)
    for m in mods:
        if m.__name__ not in _SAVED:
            _SAVED[m.__name__] = m.time
        m.time = clock
    return clock


def uninstall():
    import importlib
    for name, t in _SAVED.items():
        importlib.import_module(name).time = t
    _SAVED.clear()
