"""Q3 development: capture exact SOURCE-only Update failures, then replay without SOURCE.

Capture example:
  python research/q3/update_snapshot_dev.py capture-lr --names 'pow-k(k=4)' --out /tmp/update_snapshots.jsonl
  python research/q3/update_snapshot_dev.py capture-fresh --names mbpp/45 --tasks /path/to/opened_tasks.json --registry /path/to/registry.json --out /tmp/update_snapshots.jsonl
Replay example:
  python research/q3/update_snapshot_dev.py replay --input /tmp/update_snapshots.jsonl --out /tmp/update_replay.jsonl --cpu 5

No FRESH files are generated or opened implicitly. This is development only.
A successful component Update fit is NOT a solved task or an independent semantic verification.
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
sys.path.insert(0, "research/q3/fresh")
from neumann1 import active as ac, invention_core as ic


def canonical_sha(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_jsonl(path):
    if not pathlib.Path(path).exists():
        return []
    return [json.loads(line) for line in pathlib.Path(path).read_text().splitlines() if line.strip()]


def emit(path, row):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps(row, sort_keys=True, default=list) + "\n")
        f.flush()


def capture(args):
    if not args.names and not args.names_file:
        raise SystemExit("Explicit --names or --names-file required; do not silently expand scope.")
    if args.names_file:
        manifest = json.loads(pathlib.Path(args.names_file).read_text())
        if isinstance(manifest, dict) and "task_ids" in manifest:
            family = "list-routines" if args.mode == "capture-lr" else "fresh-dev"
            names = set(manifest["task_ids"][family])
        else:
            names = set(manifest)
    else:
        names = {args.names}
    if args.mode == "capture-lr":
        import env_listroutines as E
        import active_dev as dev
        specs = {s.name: s for s in E.tasks()}
        if not names <= specs.keys():
            raise SystemExit("Unknown list-routines task(s): " + repr(names - specs.keys()))
        jobs = [(name, specs[name], dev._h(name) % 1000) for name in sorted(names)]
    else:
        import env_fresh as EF
        if not args.tasks or not args.registry:
            raise SystemExit("Fresh capture needs existing --tasks and --registry (opened development only).")
        tasks = {t["id"]: t for t in json.loads(pathlib.Path(args.tasks).read_text())}
        registry = json.loads(pathlib.Path(args.registry).read_text())
        if not names <= (tasks.keys() & set(registry["selected"])):
            raise SystemExit("Fresh names must occur in both already-opened tasks and registry.")
        for name in names:
            # Registry hashes were defined with json.dumps(sort_keys=True) defaults.
            task_sha = hashlib.sha256(json.dumps(tasks[name], sort_keys=True).encode()).hexdigest()
            if task_sha != registry["task_sha256"][name]:
                raise SystemExit("TASK_SHA_MISMATCH " + name)
        jobs = [(name, tasks[name], int(hashlib.sha256(name.encode()).hexdigest(), 16) % 1000)
                for name in sorted(names)]

    done = {r["name"] for r in load_jsonl(args.out)
            if r.get("status") in ("ok", "inconsistent")}
    if ac.GOAL_UPDATE_SYNTH:
        raise SystemExit("Capture must use baseline synthesis (GOAL_UPDATE_SYNTH=False).")
    ac.CAPTURE_UPDATE_TRANSITIONS = True
    ac.REPAIR = False
    for name, spec, seed in jobs:
        if name in done:
            continue
        env = None
        try:
            env = E.Env(spec, 0, budget=60) if args.mode == "capture-lr" else EF.Env(spec, 0, budget=60)
            _, rec = ac.run_arm("D", env, 30.0, seed=seed)
            machines = (rec.get("formation") or {}).get("machines") or []
            failures = [m["first_update_failure"] for m in machines if m.get("first_update_failure")]
            attempts = [m["first_update_input"] for m in machines if m.get("first_update_input")]
            row = {"status": "ok", "name": name, "family": args.mode,
                   "baseline_queries": env.used, "baseline_cpu": rec.get("cpu_seconds"),
                   "failure": failures[0] if failures else None,
                   "first_attempt": attempts[0] if attempts else None,
                   "failure_count": len(failures), "no_failure_snapshot": not bool(failures)}
        except Exception as e:
            status = "inconsistent" if type(e).__name__ == "Inconsistent" else "error"
            row = {"status": status, "name": name,
                   "error": type(e).__name__ + ": " + str(e)}
        finally:
            if hasattr(env, "close"):
                env.close()
        emit(args.out, row)
        print(name, row["status"], "failure snapshot", bool(row.get("failure")), flush=True)


def tupleify(x):
    return tuple(tupleify(y) for y in x) if isinstance(x, list) else x


def try_synth(snapshot, variant, cpu):
    """Replay the Update-component ordering of active.attempt at the same CPU cap."""
    if variant not in ("baseline", "residual"):
        raise ValueError(variant)
    in_types = tuple(snapshot["in_types"])
    out_type = snapshot["output_type"]
    rows = [(tupleify(r["inputs"]), tupleify(r["output"])) for r in snapshot["rows"]]
    end = time.process_time() + cpu
    start = time.process_time()
    g, ast = None, None
    if out_type == ic.T_L:
        g, ast = ac.synth_cells(in_types, rows, end)
    if g is None and variant == "residual" and time.process_time() < end:
        r_end = time.process_time() + 0.5 * max(0.0, end - time.process_time())
        if out_type == ic.T_L:
            g, ast = ac.synth_list_delta_update(in_types, rows, r_end)
        elif out_type in (ic.T_I, ic.T_B):
            g, ast = ac.synth_goal_update(in_types, out_type, rows, r_end)
    if g is None and time.process_time() < end:
        g, ast = ac.synth_multi(in_types, out_type, rows, end)
    if g is None and out_type in (ic.T_I, ic.T_B) and time.process_time() < end:
        g, ast = ac.synth_cover(in_types, out_type, rows, end)
    elapsed = time.process_time() - start
    fit = bool(g is not None and all(g(xs) == y for xs, y in rows))
    return {"fit": fit, "ast": ast, "cpu_seconds": round(elapsed, 4),
            "row_count": len(rows)}


def replay(args):
    ac.CAPTURE_UPDATE_TRANSITIONS = False
    seen = {(r["name"], r["variant"], r["snapshot_sha256"])
            for r in load_jsonl(args.out) if r.get("status") == "ok"}
    for rec in load_jsonl(args.input):
        snapshot = rec.get("failure")
        if rec.get("status") != "ok" or snapshot is None:
            continue
        sig = snapshot["sha256"]
        if canonical_sha({k: v for k, v in snapshot.items() if k != "sha256"}) != sig:
            raise SystemExit("SNAPSHOT_SHA_MISMATCH " + rec["name"])
        for variant in ("baseline", "residual"):
            key = (rec["name"], variant, sig)
            if key in seen:
                continue
            try:
                result = try_synth(snapshot, variant, args.cpu)
                row = {"status": "ok", "name": rec["name"], "variant": variant,
                       "snapshot_sha256": sig, "cpu_cap_seconds": args.cpu, **result}
            except Exception as e:
                row = {"status": "error", "name": rec["name"], "variant": variant,
                       "snapshot_sha256": sig, "error": type(e).__name__ + ": " + str(e)}
            emit(args.out, row)
            seen.add(key)
            print(rec["name"], variant, row["status"], row.get("fit"), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("capture-lr", "capture-fresh", "replay"))
    p.add_argument("--names", help="One explicit task ID (commas inside names are preserved)")
    p.add_argument("--names-file", help="Existing JSON array of exact task IDs")
    p.add_argument("--out", required=True)
    p.add_argument("--input")
    p.add_argument("--tasks", help="Already-opened FRESH-dev task JSON, supplied locally")
    p.add_argument("--registry", help="Existing FRESH registry; hashes must match")
    p.add_argument("--cpu", type=float, default=5.0)
    args = p.parse_args()
    if args.mode == "replay":
        if not args.input or args.cpu <= 0:
            raise SystemExit("--input and positive --cpu required for replay")
        replay(args)
    else:
        capture(args)
