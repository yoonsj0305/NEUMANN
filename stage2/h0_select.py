"""H-0 student selection (stage2/DESIGN.md 7.4, 9.6: unchanged): stage2/g0_select.py (stage1/c4_select.student, the
selection-only set "select:<task>", highest accuracy; within 0.005: fewer moving heads, then the smaller restart
number) with the BOS adapter (stage2/h_adapter.py) and results/h0.

  python stage2/h0_select.py --task reverse --seed 15        # writes stage2/results/h0/selection_reverse_s15.json
"""
from __future__ import annotations
import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import h_adapter               # noqa: E402
import g0_select               # noqa: E402

g0_select.A = h_adapter        # the selection code is g0_select.main; only the adapter is the BOS one

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--seed", type=int, required=True)
    a = ap.parse_args()
    a.phase = "h0"
    g0_select.main(a)
