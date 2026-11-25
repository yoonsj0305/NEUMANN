"""3-0 token-only adapter: the G-0 adapter (stage2/g_adapter.py: vocabulary, token kinds, separators) plus the 3-0
tasks (stage3/l_tasks.py) in tasks.TASKS / tasks.SPEC / tasks.draw.  No stage-1 or stage-2 file is edited; stage-1
tasks (MQAR included) generate exactly the same data as before.

  python stage3/l_adapter.py run --task dup --kind rope --phase l30 --out-root stage3/results/3-0 --seed 0 --keep-best
"""
from __future__ import annotations
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(ROOT / "stage2"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import tasks as T                # noqa: E402  (stage 1)
import g_adapter as GA           # noqa: E402
import l_tasks as L              # noqa: E402


def install():
    GA.install()
    if getattr(T, "_l_adapter", False):
        return
    T.TASKS = tuple(T.TASKS) + tuple(t for t in L.SUITE if t not in T.TASKS)
    T.SPEC.update({t: L.SPEC[t] for t in L.SUITE})
    inner = T.draw

    def draw(task, rng, lo, hi, train_dist=False):
        if task in L.SUITE:
            return L.draw(task, rng, lo, hi, train_dist=train_dist)
        return inner(task, rng, lo, hi, train_dist=train_dist)
    T.draw = draw
    T._l_adapter = True


def run_script(name, argv):
    install()
    GA.T._g_adapter = True                                   # already installed above
    import importlib
    mod = importlib.import_module(name)
    path = ROOT / "stage1" / (name + ".py")
    src = path.read_text()
    key = 'if __name__ == "__main__":'
    block = src[src.index(key):].replace(key, "if True:", 1)
    sys.argv = [str(path)] + list(argv)
    exec(compile(block, str(path), "exec"), mod.__dict__)


if __name__ == "__main__":
    run_script(sys.argv[1], sys.argv[2:])
