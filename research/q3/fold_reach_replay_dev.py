"""DEVELOPMENT ONLY: A / B / C Update synthesis on the frozen first-failure tables (10 opened list-routines tasks).

  A  existing single-solution cell synthesis (synth_cells, first fit) for every W component
  B  existing probe-diversified candidates (synth_cells_candidates, k = 4) for the failed component, the other
     components as in A; the best initial-example fold among the candidates is reported (section 34 rule)
  C  reachability-guided, fold-constrained synthesis (synth_cells_fold) for the LAST W component (the one whose
     synthesis completes the machine, as in attempt()); earlier components as in A.  The legacy enumeration up to
     its first fit (= A); if the machine folds an initial example wrongly the same enumeration continues with
     equivalence refinement keyed by the states that fit's own fold reaches, and every later complete candidate
     is judged by all initial-example folds (first with 0 errors returned, else the best one kept)

Same table, types, initial state, per-component CPU cap and clock for every arm; no SOURCE query inside any arm.
The arms see only the frozen table T and the developer-visible initial examples.  The initial state is the
observed empty-input state from T where present, else the machine's sentinel () (attempt()).

Diagnostic evaluation AFTER each arm (never fed back): the chosen machine's agreement with the SOURCE-observed
reachable transitions R of the initial examples and its accuracy on fresh SOURCE inputs (research/q3/
reachable_state_diagnosis_dev.py; diagnostic queries, outside any budget).

  python research/q3/fold_reach_replay_dev.py --snapshots docs/experiments/dev/update_snapshots/lr.jsonl \
    --target-list docs/experiments/dev/update_snapshots/post_synthesis_first_failure.json \
    --out /tmp/fold_reach.jsonl --cpu 5 --vclock
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
import env_listroutines as E
import reachable_state_diagnosis_dev as D
from neumann1 import active as ac


def z_from_table(snap):
    root = next((a for a, e, b, u in snap.trans if u == ()), None)
    return root if root is not None else tuple(() for _ in snap.W)


def machine_errors(snap, fns, z, examples):
    errs = 0
    for (x,), y in examples:
        st = D.fold_states(snap, fns, z, x)[-1]
        errs += st is None or st[0] != y
    return errs


def reach_inputs(snap, fns, z, examples):
    """Update inputs the fold of `fns` visits on the initial examples, failing examples first (no query)."""
    fail, ok = [], []
    for (x,), y in examples:
        st, seen = z, []
        for e in snap.seq(x):
            if st is None:
                break
            seen.append(st + (e,))
            nxt = tuple(g(st + (e,)) for g in fns)
            st = None if None in nxt else nxt
        (ok if st is not None and st[0] == y else fail).append(seen)
    out = []
    for seq in fail + ok:
        out.extend(seq)
    return out


def evaluate(snap, fns, z, R, oracle, fresh):
    if fns is None:
        return {"R_fit": None, "fresh": None}
    rfit = sum(tuple(g(a + (e,)) for g in fns) == b for a, e, b, _ in R)
    ok = tot = 0
    for x in fresh:
        yt = oracle.f(x)
        if yt is None:
            continue
        st = D.fold_states(snap, fns, z, x)[-1]
        tot += 1
        ok += st is not None and st[0] == yt
    return {"R_fit": [rfit, len(R)], "fresh": [ok, tot]}


def run(args):
    if args.vclock:
        import vclock
        vclock.install(vclock.VirtualTime(), extra=(sys.modules[__name__], D))
    ac.GOAL_UPDATE_SYNTH = False
    ac.CAPTURE_UPDATE_TRANSITIONS = False
    ac.MIN_SYNTH_CPU = 0.0
    ac._inv()                                  # cache outside every timed region (identical for all arms)
    snapshots = D.read_rows(args.snapshots)
    targets = set(json.loads(pathlib.Path(args.target_list).read_text()))
    specs = {s.name: s for s in E.tasks()}
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {r["name"] for r in D.read_rows(out)} if out.exists() else set()
    for rec in snapshots:
        name = rec["name"]
        if name not in targets or name in done or rec.get("failure") is None or rec["failure"]["output_type"] != "L":
            continue
        snap = D.Snapshot(rec["failure"])
        examples = E.Env(specs[name], 0, budget=60).initial()
        z = z_from_table(snap)
        T = snap.trans
        res = {"name": name, "snapshot_sha256": snap.raw["sha256"], "scope": "DEVELOPMENT_ONLY_NO_SOURCE_IN_ARMS",
               "clock": "virtual" if args.vclock else "process_time", "cpu_cap_per_component": args.cpu,
               "W": [list(w) for w in snap.W], "z": D.thaw(z), "failed_component": snap.failed}
        # ---- A
        c0 = time.process_time()
        a_fns, a_asts, _ = D.synth_all(snap, T, args.cpu)
        res["A"] = {"fit": a_fns is not None, "ast": [a[1] if a else None for a in a_asts],
                    "cpu": round(time.process_time() - c0, 3),
                    "fold_errors": machine_errors(snap, a_fns, z, examples) if a_fns else None}
        # ---- B (failed component only, others from A)
        c0 = time.process_time()
        j = snap.failed
        b_best, b_n = None, 0
        if a_fns is not None:
            cands = ac.synth_cells_candidates(snap.in_types, D.rows_of(T, j), time.process_time() + args.cpu, k=4)
            b_n = len(cands)
            for g, ast in cands:
                fns = list(a_fns)
                fns[j] = g
                e = machine_errors(snap, fns, z, examples)
                if b_best is None or e < b_best[0]:
                    b_best = (e, fns, ast)
        res["B"] = {"candidates": b_n, "cpu": round(time.process_time() - c0, 3),
                    "fold_errors": b_best[0] if b_best else None, "ast": b_best[2][1] if b_best else None}
        # ---- C: components before the last as in A; the last component by the fold-constrained search with the
        # same per-component cap (its first candidate is the legacy first fit; the search continues from there)
        c0 = time.process_time()
        c_fns, c_info, c_asts = None, None, [None] * len(snap.W)
        fns, ok = [], True
        m = len(snap.W)
        for k in range(m - 1):
            start = time.process_time()
            g, ast = ac.synth_cells(snap.in_types, D.rows_of(T, k), start + args.cpu)
            if g is None:
                ok = False
                break
            fns.append(g)
            c_asts[k] = ast
        if ok:
            def ferr(g):
                return machine_errors(snap, fns + [g], z, examples)

            def rin(g):
                return reach_inputs(snap, fns + [g], z, examples)
            start = time.process_time()
            g, ast, c_info = ac.synth_cells_fold(snap.in_types, D.rows_of(T, m - 1), start + args.cpu, ferr, rin)
            if g is not None:
                c_fns = fns + [g]
                c_asts[m - 1] = ast
        res["C"] = {"fit": c_fns is not None, "ast": [a[1] if a else None for a in c_asts],
                    "cpu": round(time.process_time() - c0, 3), "search": c_info,
                    "first_equals_A": bool(c_info) and c_info.get("first") == (a_asts[-1][1] if a_fns else None),
                    "fold_errors": machine_errors(snap, c_fns, z, examples) if c_fns else None}
        # ---- diagnostic evaluation (SOURCE, outside the arms)
        oracle = D.Oracle(specs[name])
        R, _ = D.reachable(snap, oracle, examples)
        fresh = D.fresh_inputs(snap, examples, args.fresh, 12345)
        res["A"].update(evaluate(snap, a_fns, z, R, oracle, fresh))
        res["B"].update(evaluate(snap, b_best[1] if b_best else None, z, R, oracle, fresh))
        res["C"].update(evaluate(snap, c_fns, z, R, oracle, fresh))
        res["diagnostic_source_queries"] = oracle.queries
        with open(out, "a") as fh:
            fh.write(json.dumps(res, sort_keys=True) + "\n")
        print(name, "| fold A/B/C", res["A"]["fold_errors"], res["B"]["fold_errors"], res["C"]["fold_errors"],
              "| fresh A/B/C", res["A"]["fresh"], res["B"]["fresh"], res["C"]["fresh"],
              "| cpu A/B/C", res["A"]["cpu"], res["B"]["cpu"], res["C"]["cpu"],
              "| C tested", (c_info or {}).get("tested"), "first=A", res["C"]["first_equals_A"], flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--snapshots", required=True)
    p.add_argument("--target-list", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--cpu", type=float, default=5.0)
    p.add_argument("--fresh", type=int, default=20)
    p.add_argument("--vclock", action="store_true")
    run(p.parse_args())
