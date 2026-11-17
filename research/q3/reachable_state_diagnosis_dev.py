"""DEVELOPMENT ONLY: reachable-state diagnosis of Q3 fold failures (opened list-routines, 10 list-cell snapshots).

Question (directive "Reachability-Guided Structural Synthesis", P0-B / P0-C): the Update adopted on the frozen
first-failure transition table T fits T but folds wrongly on initial examples.  WHY?

For each snapshot the script separates
  * the artificial states of T (the agent's own trajectories + localisation points), and
  * the states the fold of every INITIAL example actually reaches: S(u) = (f(u.w) for w in W) on every prefix u of
    every initial input.  These are OBSERVED FROM SOURCE by diagnostic queries (an unlimited diagnostic Env with the
    same seed; hidden test inputs stay blocked, the routine and hidden tests are never read).  The diagnostic
    queries are NOT part of any agent budget and are reported separately.

and records, per task
  1. the first reachable step where the adopted Update leaves the true state (and whether that (state, element)
     lies inside what T observed: seen state / seen element / longer state than T ever showed);
  2. W-sufficiency evidence: equal (state, element) with different observed successors on T u R (a conflict is a
     proof that the fixed W cannot carry the needed information; no conflict is NOT a proof of sufficiency);
  3. readout check (observed f(x) equals the initial example's answer);
  4. initial state: observed S(()) or the machine's sentinel when it is undefined / blocked;
  5. representability under the existing cell synthesiser: synth_cells on T u R (all observed) with a diagnostic
     CPU cap; a fit there is a program in the existing language that reproduces every reachable transition, hence
     every initial example fold, and it is then checked on fresh SOURCE inputs (diagnostic) for generalisation.

Never used to choose anything inside the agent.  No sealed FRESH/FORMAL data is read.

  python research/q3/reachable_state_diagnosis_dev.py \
    --snapshots docs/experiments/dev/update_snapshots/lr.jsonl \
    --target-list docs/experiments/dev/update_snapshots/post_synthesis_first_failure.json \
    --out /tmp/reachable.jsonl --cpu 5 --diag-cpu 20
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import random
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


def thaw(x):
    return [thaw(i) for i in x] if isinstance(x, tuple) else x


class Snapshot:
    """The frozen first-failure transition system of one task (no query)."""

    def __init__(self, snap):
        if digest({k: v for k, v in snap.items() if k != "sha256"}) != snap["sha256"]:
            raise SystemExit("SNAPSHOT_SHA256_MISMATCH")
        self.raw = snap
        self.W = [tuple(w) for w in snap["W"]]
        self.direction = snap["direction"]
        self.in_types = tuple(snap["in_types"])
        self.trans = [(freeze(t["state"]), t["element"], freeze(t["successor"]), freeze(t["prefix"]))
                      for t in snap["transitions"]]
        self.failed = snap["failed_component"]

    def cont(self, u, w):
        return tuple(u) + tuple(w) if self.direction == "prefix" else tuple(w) + tuple(u)

    def step_input(self, u, e):
        return tuple(u) + (e,) if self.direction == "prefix" else (e,) + tuple(u)

    def seq(self, x):
        return tuple(x) if self.direction == "prefix" else tuple(x)[::-1]

    def prefixes(self, x):
        out = [()]
        for e in self.seq(x):
            out.append(self.step_input(out[-1], e))
        return out


def rows_of(trans, j):
    return [(a + (e,), b[j]) for a, e, b, *_ in trans]


def synth_all(snap, trans, cpu, synth=None):
    """One Update per W component on the given transitions (the attempt() order); returns (fns, asts, seconds)."""
    synth = synth or ac.synth_cells
    fns, asts = [], []
    t0 = time.process_time()
    for j in range(len(snap.W)):
        start = time.process_time()
        g, ast = synth(snap.in_types, rows_of(trans, j), start + cpu)
        if g is None:
            return None, asts + [None], time.process_time() - t0
        fns.append(g)
        asts.append(ast)
    return fns, asts, time.process_time() - t0


def fold_states(snap, fns, z, x):
    states = [z]
    for e in snap.seq(x):
        st = states[-1]
        if st is None:
            states.append(None)
            continue
        nxt = tuple(g(st + (e,)) for g in fns)
        states.append(None if None in nxt else nxt)
    return states


class Oracle:
    """Diagnostic SOURCE access (development only; counted, never given to the agent)."""

    def __init__(self, spec):
        self.env = E.Env(spec, 0, budget=10 ** 9)
        self.memo = {}

    def f(self, x):
        x = tuple(x)
        if x not in self.memo:
            self.memo[x] = self.env.query(x)
        return self.memo[x]

    @property
    def queries(self):
        return len(self.memo)


def true_state(snap, oracle, u):
    s = tuple(oracle.f(snap.cont(u, w)) for w in snap.W)
    return None if None in s else s


def reachable(snap, oracle, examples):
    """Observed reachable transitions of every initial example's fold: (state, e, successor, prefix)."""
    out, per_example = [], []
    for (x,), y in examples:
        ps = snap.prefixes(x)
        sts = [true_state(snap, oracle, u) for u in ps]
        per_example.append((x, y, ps, sts))
        for i, e in enumerate(snap.seq(x)):
            if sts[i] is not None and sts[i + 1] is not None:
                out.append((sts[i], e, sts[i + 1], ps[i]))
    return out, per_example


def conflicts(trans):
    by = {}
    found = []
    for a, e, b, u in trans:
        if (a, e) in by and by[(a, e)][0] != b:
            found.append({"state": thaw(a), "element": e, "successors": [thaw(by[(a, e)][0]), thaw(b)],
                          "prefixes": [thaw(by[(a, e)][1]), thaw(u)]})
        by.setdefault((a, e), (b, u))
    return found


def dedup(trans):
    seen, out = set(), []
    for t in trans:
        k = (t[0], t[1])
        if k not in seen:
            seen.add(k)
            out.append(t)
    return out


def machine_z(snap, oracle):
    """attempt(): the observed empty-input state, else (list answer) the sentinel ()."""
    vals = [oracle.f(snap.cont((), w)) for w in snap.W]
    return tuple(() if v is None else v for v in vals), [v is not None for v in vals]


def divergence(snap, fns, z, per_example, tset):
    seen_states = {a for a, *_ in tset}
    seen_elems = {e for _, e, *_ in tset}
    max_len = max((len(a[0]) for a, *_ in tset if isinstance(a[0], tuple)), default=0)
    pairs = {(a, e) for a, e, *_ in tset}
    out = []
    for x, y, ps, sts in per_example:
        pred = fold_states(snap, fns, z, x)
        final = pred[-1][0] if pred[-1] is not None else None
        rec = {"input": list(x), "expected": thaw(y), "predicted": thaw(final), "correct": final == y}
        if final != y:
            k = next((i for i in range(len(sts)) if sts[i] is not None and pred[i] != sts[i]), None)
            if k is None:
                rec["first_divergence"] = "UNOBSERVABLE (true states undefined on the path)"
            elif k == 0:
                rec["first_divergence"] = {"step": 0, "kind": "initial state"}
            else:
                a, e = sts[k - 1], snap.seq(x)[k - 1]
                rec["first_divergence"] = {
                    "step": k, "prefix": thaw(ps[k - 1]), "state": thaw(a), "element": e,
                    "true_successor": thaw(sts[k]), "predicted_successor": thaw(pred[k]),
                    "previous_state_correct": pred[k - 1] == a,
                    "pair_in_T": (a, e) in pairs, "state_in_T": a in seen_states, "element_in_T": e in seen_elems,
                    "state_len": len(a[0]) if a is not None and isinstance(a[0], tuple) else None,
                    "state_longer_than_T": a is not None and isinstance(a[0], tuple) and len(a[0]) > max_len}
        out.append(rec)
    return out, max_len


def fresh_inputs(snap, examples, n, seed):
    """Diagnostic generalisation inputs (lengths and values from the initial examples only)."""
    rng = random.Random(seed)
    vals = sorted({v for (x,), _ in examples for v in x}) or list(range(10))
    lens = [len(x) for (x,), _ in examples]
    xs, tries = [], 0
    while len(xs) < n and tries < 1000:
        tries += 1
        L = rng.randint(min(lens), max(lens) + 2)
        x = tuple(rng.choice(range(min(vals), max(vals) + 1)) for _ in range(L))
        if x not in xs and all(x != ex for (ex,), _ in examples):
            xs.append(x)
    return xs


def run(args):
    if args.vclock:
        import vclock
        vclock.install(vclock.VirtualTime(), extra=(sys.modules[__name__],))
    snapshots = read_rows(args.snapshots)
    targets = set(json.loads(pathlib.Path(args.target_list).read_text()))
    spec_by_name = {spec.name: spec for spec in E.tasks()}
    ac.GOAL_UPDATE_SYNTH = False
    ac.CAPTURE_UPDATE_TRANSITIONS = False
    ac.MIN_SYNTH_CPU = 0.0
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = {r["name"] for r in read_rows(out_path)} if out_path.exists() else set()
    for rec in snapshots:
        name = rec["name"]
        if name not in targets or name in done or rec.get("failure") is None:
            continue
        raw = rec["failure"]
        if raw["output_type"] != "L":
            continue                       # the 11th case (foldrI integer Update) is outside the cell mechanism
        snap = Snapshot(raw)
        spec = spec_by_name[name]
        examples = E.Env(spec, 0, budget=60).initial()      # developer-visible initial examples only
        oracle = Oracle(spec)
        T = snap.trans
        # A: the adopted first-fit Update on T (the existing synthesiser, fixed CPU)
        fns, asts, sec = synth_all(snap, T, args.cpu)
        z, z_obs = machine_z(snap, oracle)
        R, per_example = reachable(snap, oracle, examples)
        TR = dedup(T + R)
        res = {"name": name, "snapshot_sha256": raw["sha256"], "scope": "DEVELOPMENT_ONLY_DIAGNOSTIC",
               "clock": "virtual" if args.vclock else "process_time",
               "W": [list(w) for w in snap.W], "direction": snap.direction,
               "T_transitions": len(T), "T_root_observed": any(u == () for *_, u in T),
               "z": thaw(z), "z_observed": z_obs,
               "readout_ok": all(oracle.f(x) == y for (x,), y in examples),
               "A_fit": fns is not None, "A_ast": [a[1] if isinstance(a, tuple) else None for a in asts],
               "A_cpu": round(sec, 3)}
        res["R_transitions"] = len(R)
        res["R_new_pairs"] = len({(a, e) for a, e, *_ in R} - {(a, e) for a, e, *_ in T})
        res["conflicts_T"] = conflicts(T)
        res["conflicts_TR"] = conflicts(T + R)
        res["undefined_reachable_states"] = sum(s is None for *_, sts in per_example for s in sts)
        if fns is not None:
            div, max_len = divergence(snap, fns, z, per_example, T)
            res["T_max_state_len"] = max_len
            res["A_fold_errors"] = sum(not d["correct"] for d in div)
            res["A_divergences"] = [d for d in div if not d["correct"]]
            res["A_R_fit"] = sum(tuple(g(a + (e,)) for g in fns) == b for a, e, b, _ in R)
        # Representability probe: the existing synthesiser on everything observed (T u R), diagnostic CPU cap
        if not res["conflicts_TR"]:
            fns2, asts2, sec2 = synth_all(snap, TR, args.diag_cpu)
            res["TR_fit"] = fns2 is not None
            res["TR_ast"] = [a[1] if isinstance(a, tuple) else None for a in asts2]
            res["TR_cpu"] = round(sec2, 3)
            if fns2 is not None:
                div2, _ = divergence(snap, fns2, z, per_example, T)
                res["TR_fold_errors"] = sum(not d["correct"] for d in div2)
                xs = fresh_inputs(snap, examples, args.fresh, 12345)
                ok = tot = 0
                for x in xs:
                    yt = oracle.f(x)
                    if yt is None:
                        continue
                    st = fold_states(snap, fns2, z, x)[-1]
                    tot += 1
                    ok += st is not None and st[0] == yt
                res["TR_fresh_correct"] = [ok, tot]
        res["diagnostic_source_queries"] = oracle.queries
        with open(out_path, "a") as fh:
            fh.write(json.dumps(res, sort_keys=True) + "\n")
        print(name, "| A fold err", res.get("A_fold_errors"), "| R", len(R), "new", res["R_new_pairs"],
              "| conflicts T/TR", len(res["conflicts_T"]), len(res["conflicts_TR"]),
              "| TR fit", res.get("TR_fit"), "fold", res.get("TR_fold_errors"), "fresh", res.get("TR_fresh_correct"),
              "| diag q", oracle.queries, flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--snapshots", required=True)
    p.add_argument("--target-list", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--cpu", type=float, default=5.0)
    p.add_argument("--diag-cpu", type=float, default=20.0)
    p.add_argument("--fresh", type=int, default=20)
    p.add_argument("--vclock", action="store_true", help="deterministic virtual CPU clock (research/q3/vclock.py)")
    run(p.parse_args())
