"""DEVELOPMENT ONLY: exactness and real-CPU effect of latent.COVER_MEMO on fixed Update tables (no SOURCE query).

Tables: the 10 list-cell first-failure snapshots of the section 31 tasks (section 29 format) (docs/experiments/dev/update_snapshots/lr.jsonl) and
any extra snapshot JSON files given (policy-E tables captured with research/q3/budgeted_reach_case2_dev.py).
  exactness  virtual clock (research/q3/vclock.py; the cover scans do not move deadlines): synth_cells with the memo
             off and on must return the same program at the same cap
  speed      real time.process_time(): CPU used and fit at fixed caps, memo off vs on, alternating order

  python research/q3/cover_memo_check_dev.py --caps 5,10,40 --out rows.jsonl [extra_snapshot.json ...]
"""
from __future__ import annotations
import argparse
import json
import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from neumann1 import active as ac, latent as lt


def freeze(x):
    return tuple(freeze(i) for i in x) if isinstance(x, list) else x


def tables(extra):
    out = []
    targets = set(json.load(open("docs/experiments/dev/update_snapshots/post_synthesis_first_failure.json")))
    for l in open("docs/experiments/dev/update_snapshots/lr.jsonl"):
        r = json.loads(l)
        f = r.get("failure")
        if f and f["output_type"] == "L" and r["name"] in targets:
            out.append((r["name"], f))
    for p in extra:
        f = json.load(open(p))
        out.append((p.split("/")[-1], f))
    return out


def synth(f, cap, memo):
    lt.COVER_MEMO = memo
    rows = [(freeze(r["inputs"]), freeze(r["output"])) for r in f["rows"]]
    t0 = time.process_time()
    g, ast = ac.synth_cells(tuple(f["in_types"]), rows, t0 + cap)
    lt.COVER_MEMO = False
    return g is not None, (ast[1] if ast else None), round(time.process_time() - t0, 3)


def main(a):
    ac._inv()
    tabs = tables(a.extra)
    caps = [float(c) for c in a.caps.split(",")]
    out = open(a.out, "a")
    import vclock
    clock = vclock.install(vclock.VirtualTime(), extra=(sys.modules[__name__],))
    for name, f in tabs:
        x0, x1 = synth(f, 5.0, False), synth(f, 5.0, True)
        rec = {"name": name, "check": "exactness_virtual_5s", "off": x0[:2], "on": x1[:2], "identical": x0[:2] == x1[:2]}
        out.write(json.dumps(rec) + "\n"); out.flush()
        print("exact", name[:40], rec["identical"], x0[0], x1[0], flush=True)
    vclock.uninstall()
    for name, f in tabs:
        for cap in caps:
            res = {}
            for memo in ((False, True) if hash(name) % 2 else (True, False)):
                res[memo] = synth(f, cap, memo)
            rec = {"name": name, "check": "speed_real", "cap": cap,
                   "off": {"fit": res[False][0], "cpu": res[False][2], "ast": res[False][1]},
                   "on": {"fit": res[True][0], "cpu": res[True][2], "ast": res[True][1]}}
            out.write(json.dumps(rec) + "\n"); out.flush()
            print("speed", name[:40], cap, "off", res[False][0], res[False][2], "on", res[True][0], res[True][2], flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--caps", default="5,10,40")
    p.add_argument("--out", required=True)
    p.add_argument("extra", nargs="*")
    main(p.parse_args())
