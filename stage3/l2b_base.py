"""L2b-0 baselines (stage3/DESIGN.md 11.10-2): multi_add and mulNM (stage3/r_tasks.py, the R draw and bins), seed 0,
1M, N = 100,000, the stage-1 protocol (stage1/run.py unchanged, through stage3/r_adapter.py; evaluation in-distribution
1,000, every out-of-distribution bin 500, stage-1 seeds; judgment = the stage-1 rule).

  stage-1 kinds  abacus, rope, looped_rr, gru         stage1/run.py via r_adapter (as 3-0 C), --keep-best
  3-B kinds      rel_rand, nope                       stage3/pe3b.py run (PATCHES unchanged), LR x0.5 / x2 by 8.5-3
                 rel_rand P_MAX (the position range {0..P_MAX-1}): the 3-B value 512 when the longest evaluation
                 sequence fits, else the smallest multiple of 256 >= the longest evaluation sequence (multi_add)
                 -- recorded choice (rule 4: the randomized range must cover the test lengths, Ruoss et al. 2023).
Memory RNNs (10.5 format): stage3/l2b_p0.py.

  python stage3/l2b_base.py run --task multi_add|mulNM --kind K [--lr-mult M] [--resume]
  python stage3/l2b_base.py pmax --task T
"""
from __future__ import annotations
import argparse
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(ROOT / "stage2"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

OUT = pathlib.Path(os.environ.get("L2B_BASE_OUT", HERE / "results" / "L2b-0" / "baselines"))
STAGE1 = ("abacus", "rope", "looped_rr", "gru")
PE3B = ("rel_rand", "nope")


def longest_eval(task):
    import r_adapter
    r_adapter.install()
    import tasks as T
    ev = T.eval_sets(task, 1000, 500)
    return max(len(p) + len(a) for v in ev.values() for p, a in v)


def pmax(task):
    n = longest_eval(task)
    return 512 if n <= 512 else 256 * ((n + 255) // 256)


def cmd_run(a):
    OUT.mkdir(parents=True, exist_ok=True)
    if a.kind in STAGE1:
        assert a.lr_mult == 1.0
        import r_adapter
        argv = ["--task", a.task, "--kind", a.kind, "--phase", "l2b0", "--out-root", str(OUT), "--seed", "0",
                "--scale", "1M", "--N", "100000", "--threads", "1", "--keep-best"]
        if a.resume:
            argv.append("--resume")
        if os.environ.get("L2B_BASE_SMOKE"):                 # smoke test only (scratch out-root)
            argv += ["--max-steps", os.environ["L2B_BASE_SMOKE"], "--eval-every", os.environ["L2B_BASE_SMOKE"]]
        r_adapter.run_script("run", argv)
        return
    import pe3b
    import r_adapter
    if a.kind == "rel_rand":
        pe3b.P_MAX = pmax(a.task)
        print("rel_rand P_MAX", pe3b.P_MAX, flush=True)
    pe3b.ADAPTER[a.task] = "r"
    pe3b.install_adapter = lambda task: r_adapter.install()
    os.environ["PE3B_OUT"] = str(OUT)
    if os.environ.get("L2B_BASE_SMOKE"):
        os.environ["PE3B_SMOKE"] = os.environ["L2B_BASE_SMOKE"]
    pe3b.cmd_run(a)


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    q = sp.add_parser("run")
    q.add_argument("--task", choices=("multi_add", "mulNM"), required=True)
    q.add_argument("--kind", choices=STAGE1 + PE3B, required=True)
    q.add_argument("--lr-mult", type=float, default=1.0)
    q.add_argument("--resume", action="store_true")
    q = sp.add_parser("pmax")
    q.add_argument("--task", choices=("multi_add", "mulNM"), required=True)
    a = p.parse_args()
    if a.cmd == "pmax":
        print(a.task, longest_eval(a.task), pmax(a.task))
        return
    cmd_run(a)


if __name__ == "__main__":
    main()
