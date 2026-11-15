"""DEVELOPMENT ONLY: fixed-transition latent cell alternatives (list-routines).

Reads frozen, already-opened Gate E snapshots and the existing initial
development examples. Never calls SOURCE.query or reads a hidden test.
Two matched 5-CPU-second synthesiser calls are run per eligible snapshot.
This is NOT a full machine or generalisation evaluation.

  python research/q3/latent_candidate_replay_dev.py \
    --snapshots docs/experiments/dev/update_snapshots/lr.jsonl \
    --target-list docs/experiments/dev/update_snapshots/post_synthesis_first_failure.json \
    --out /tmp/latent_candidate_lr11.jsonl --cpu 5 --k 4
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
import env_listroutines as E
from neumann1 import active as ac


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read_rows(path):
    return [json.loads(line) for line in pathlib.Path(path).read_text().splitlines() if line.strip()]


def freeze(x):
    return tuple(freeze(i) for i in x) if isinstance(x, list) else x


def fold_errors(fn, snapshot, examples):
    """Only W=[()] with no invented accumulator and observed root is evaluable
    without the missing other component's Update or asking SOURCE.
    """
    if snapshot["W"] != [[]] or snapshot["accumulators"]:
        return None, "NEEDS_OTHER_COMPONENT_UPDATES"
    roots = [tr for tr in snapshot["transitions"] if tr["prefix"] == []]
    if not roots:
        return None, "ROOT_STATE_UNOBSERVED"
    z = freeze(roots[0]["state"])
    if len(z) != 1:
        return None, "NOT_SINGLE_COMPONENT"
    errors = 0
    for (x,), expected in examples:
        state = z
        seq = x if snapshot["direction"] == "prefix" else x[::-1]
        for e in seq:
            y = fn(state + (e,))
            state = (y,)
            if y is None:
                break
        if state[0] != expected:
            errors += 1
    return errors, "INITIAL_EXAMPLES_ONLY"


def run(args):
    snapshots = read_rows(args.snapshots)
    targets = set(json.loads(pathlib.Path(args.target_list).read_text()))
    spec_by_name = {spec.name: spec for spec in E.tasks()}
    done = {r["name"] for r in read_rows(args.out)} if pathlib.Path(args.out).exists() else set()
    ac.GOAL_UPDATE_SYNTH = False
    ac.CAPTURE_UPDATE_TRANSITIONS = False
    ac.MIN_SYNTH_CPU = 0.0
    for rec in snapshots:
        name = rec["name"]
        if name not in targets or name in done:
            continue
        snap = rec.get("failure")
        if snap is None:
            continue
        if digest({k: v for k, v in snap.items() if k != "sha256"}) != snap["sha256"]:
            raise SystemExit("SNAPSHOT_SHA256_MISMATCH " + name)
        rows = [(freeze(r["inputs"]), freeze(r["output"])) for r in snap["rows"]]
        types = tuple(snap["in_types"])
        if snap["output_type"] != "L":
            continue
        # E.Env.initial returns only developer-visible initial examples; hidden
        # E.Env._test is never accessed, and query() is never invoked.
        env = E.Env(spec_by_name[name], 0, budget=60)
        examples = env.initial()
        start = time.process_time()
        base_fn, base_ast = ac.synth_cells(types, rows, start + args.cpu)
        base_seconds = time.process_time() - start
        start = time.process_time()
        alternatives = ac.synth_cells_candidates(types, rows, start + args.cpu, k=args.k)
        alt_seconds = time.process_time() - start
        base_fold = fold_errors(base_fn, snap, examples) if base_fn else (None, "NO_BASELINE_UPDATE")
        generated = []
        for fn, ast in alternatives:
            e, reason = fold_errors(fn, snap, examples)
            generated.append({"ast": repr(ast), "fold_errors": e, "fold_status": reason,
                              "transition_fit": all(fn(i) == y for i, y in rows)})
        measured = [d["fold_errors"] for d in generated if d["fold_errors"] is not None]
        result = {"name": name, "snapshot_sha256": snap["sha256"],
                  "scope": "DEVELOPMENT_ONLY_NO_SOURCE_QUERY",
                  "cpu_cap_per_arm": args.cpu, "k": args.k,
                  "baseline_fit": base_fn is not None,
                  "baseline_ast": repr(base_ast) if base_ast else None,
                  "baseline_cpu_seconds": round(base_seconds, 4),
                  "baseline_fold_errors": base_fold[0],
                  "baseline_fold_status": base_fold[1],
                  "alternative_cpu_seconds": round(alt_seconds, 4),
                  "candidate_count": len(generated),
                  "candidates": generated,
                  "best_candidate_fold_errors": min(measured) if measured else None,
                  "whole_task_solved": "NOT_EVALUATED",
                  "original_semantics": "UNKNOWN"}
        pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "a") as fh:
            fh.write(json.dumps(result, sort_keys=True) + "\n")
            fh.flush()
        print(name, "baseline_fit", base_fn is not None,
              "alternatives", len(generated), "best_fold", result["best_candidate_fold_errors"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshots", required=True)
    parser.add_argument("--target-list", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--cpu", type=float, default=5.0)
    parser.add_argument("--k", type=int, default=4)
    args = parser.parse_args()
    if args.cpu <= 0 or args.k < 2 or args.k > 4:
        parser.error("Positive CPU and 2 <= k <= 4 required.")
    run(args)
