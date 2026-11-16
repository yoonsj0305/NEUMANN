"""DEVELOPMENT ONLY: A / D / E whole-machine comparison with SOURCE-cost decomposition (real CPU clock).

  A  existing structural discovery (synthetic state trajectories)                     REACH_TRAJ = False
  D  every initial example's reachable states as the trajectories                      REACH_TRAJ = True
  E  synthetic trajectories + a budgeted, priority-selected subset of the initial
     examples' reachable transitions (at most REACH_BUDGET = 20 SOURCE queries)        BUDGETED_REACH_TRAJ = True

Everything else is identical: synthesiser, state grammar, independent challenge, fallbacks, 60 SOURCE queries,
30 CPU s (time.process_time()), run_arm("D") exactly as research/q3/active_dev.job.  Each (arm, task, seed) runs
in a fresh process.  Instrumentation (no effect on decisions): active.QUERY_HOOK sees every formation-state query
call, cached or not; a wrapper on env.query records every SOURCE charge and the phase it belongs to.
Solved = hidden test of the opened development task (evaluation only); optional diagnostic semantic check on random
SOURCE inputs from a separate Env (outside the budget).

  python research/q3/budgeted_reach_dev.py --names-file names.json --arms A,D,E --seeds base --out rows.jsonl
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


def h(s):
    return int(hashlib.sha256(s.encode()).hexdigest(), 16)


def set_arm(arm):
    ac.GOAL_UPDATE_SYNTH = False
    ac.CAPTURE_UPDATE_TRANSITIONS = False
    ac.MIN_SYNTH_CPU = 0.0
    ac.REPAIR = False
    ac.FOLD_REACH_SYNTH = False
    ac.REACH_TRAJ = arm == "D"
    ac.BUDGETED_REACH_TRAJ = arm in ("E", "E2", "EF", "EFb", "EFc", "EFbc")
    ac.REACH_MODE = "augment" if arm == "E2" else "replace"
    # CASE-2 arms (section 38): EFb = E + one-shot synthetic fallback after a reachable-table Update failure;
    # EFc = E + the existing per-round synthesis CPU floor (10 s, a reallocation inside the same formation deadline);
    # EFbc = both.  AF / EF are the section 36 follow-up names (AF = A + floor, EF = EFc).
    ac.E_SYNTH_FALLBACK = arm in ("EFb", "EFbc")
    ac.MIN_SYNTH_CPU = 10.0 if arm in ("AF", "EF", "EFc", "EFbc", "PF") else 0.0
    # Predictive State Invention arms (section 39): P = PSI; Pno = PSI with the discovered latent withheld (same
    # distinction experiments); Pl = PSI with the learned discovery policy (weights from NEUMANN_PSI_POLICY);
    # PF = P + the existing synthesis floor (a reallocation control)
    ac.PSI = arm in ("P", "Pno", "Pl", "PF")
    ac.PSI_ABLATE = arm == "Pno"
    # section 40: Q = PSI40 (structural state identification at the existing path's give-up points, with budget and
    # necessity checks); Qno = PSI40 with the identified state withheld (same experiments)
    ac.PSI40 = arm in ("Q", "Qno", "R", "Rno", "J", "Jno")
    ac.PSI40_ABLATE = arm in ("Qno", "Rno")
    # section 41: R = PSI40 + evidence-driven structural identification (PSI41); Rno = R with the state withheld
    ac.PSI41 = arm in ("R", "Rno", "J", "Jno")
    # section 43: J = R + joint latent invention (PSI43); Jno = J with the jointly constructed machine withheld
    ac.PSI43 = arm in ("J", "Jno")
    ac.PSI43_ABLATE = arm in ("Jno", "JFno")
    # JF = the joint core as the primary path (then the R path with what is left); JFno = JF, machine withheld
    ac.PSI43_FIRST = arm in ("JF", "JFno")
    if arm in ("JF", "JFno"):
        ac.PSI40, ac.PSI41 = True, True
    # section 44: K = the FACTORED joint core as the primary path (then the R path with what is left); Kno = K with
    # the factored machine withheld (same prefix queries and experiments)
    ac.PSI44_FIRST = arm in ("K", "Kno")
    ac.PSI44_ABLATE = arm == "Kno"
    if arm in ("K", "Kno"):
        ac.PSI40, ac.PSI41 = True, True
    # the answer-length stage of the cell construction gets >= 1.5 s (a reallocation inside the same deadline) in
    # Q, Qno and the control AL = A + the same floor (separates the floor from the identified state)
    from neumann1 import latent as _lt
    _lt.LENGTH_FLOOR = 1.5 if arm in ("Q", "Qno", "AL", "R", "Rno", "J", "Jno", "JF", "JFno", "K", "Kno") else 0.0
    # counterexample repair of a refuted machine (the existing in-place rule, section 22): part of PSI (P0-D) for
    # every PSI arm; AR = A + the same rule (the control that separates repair from the latent)
    ac.REPAIR = "inplace" if arm in ("P", "Pno", "Pl", "PF", "AR", "Q", "Qno", "R", "Rno", "J", "Jno", "JF", "JFno", "K", "Kno") else False
    ac.PSI_POLICY = None
    if arm == "Pl":
        import os
        ac.PSI_POLICY = json.loads(pathlib.Path(os.environ["NEUMANN_PSI_POLICY"]).read_text())["weights"]


def last_elem(u, direction):
    return None if not u else (u[-1] if direction == "prefix" else u[0])


def classify(calls, charges):
    """Per charged SOURCE query: the cost category (P0-A).  Formation state queries are classified in the order
    they were charged, per machine direction: initial state / added state component / new length / new element /
    known region (a new pair in already-covered lengths and elements)."""
    cat = {}
    seen = {}
    for c in charges:
        k = c["category_tag"]
        if c["phase"] != "formation":
            cat[c["phase"]] = cat.get(c["phase"], 0) + 1
            continue
        if k in ("states", "reach") and c.get("ctx"):
            u, w = c["ctx"]
            d = c["direction"]
            s = seen.setdefault(d, {"lens": set(), "elems": set()})
            if not u:
                key = "initial_state"
            elif w:
                key = "state_component"
            elif len(u) not in s["lens"] and len(u) > max(s["lens"] | {0}):
                key = "new_length"
            elif last_elem(u, d) not in s["elems"]:
                key = "new_element"
            else:
                key = "known_region"
            s["lens"].add(len(u))
            s["elems"].add(last_elem(u, d))
            key = ("reach:" if k == "reach" else "states:") + key
        elif k == "candidate":
            key = "state_component_screen"
        elif k == "localise":
            key = "localise"
        elif k == "selftest":
            key = "selftest"
        else:
            key = "formation:" + str(k)
        cat[key] = cat.get(key, 0) + 1
    return cat


def reachable_observed(initial, log, direction="prefix"):
    """Distinct reachable transitions of the initial examples whose parent and child answers are both known
    (answer component; from the query log and the initial examples)."""
    known = {tuple(x): y for (x,), y in initial}
    for x, y in log:
        if y is not None and not isinstance(y, str):
            known[tuple(x)] = y
    n, tot = 0, 0
    for (x,), _ in initial:
        x = tuple(x)
        for i in range(1, len(x) + 1):
            p, c = (x[:i - 1], x[:i]) if direction == "prefix" else (x[len(x) - i + 1:], x[len(x) - i:])
            tot += 1
            n += p in known and c in known
    return n, tot


def semantic(spec, pred, n=300, seed=777):
    oracle = E.Env(spec, 0, budget=10 ** 9)
    rng = random.Random(seed)
    ok = tot = 0
    for _ in range(n):
        x = tuple(rng.randrange(0, 17) for _ in range(rng.randrange(0, 10)))
        y = oracle.query(x)
        if y is None:
            continue
        tot += 1
        ok += pred((x,)) == y
    return [ok, tot]


EVAL_SET = "docs/experiments/dev/case2_recovery/eval_set.json"
PSI_EVAL_SET = "docs/experiments/dev/psi/eval_set.json"
PSI40_EVAL_SET = "docs/experiments/dev/psi40/eval_set.json"


def registered():
    """name -> committed sha256 of every pre-registered task (section 38 set, and the section 39 set once committed)."""
    reg = json.loads(pathlib.Path(EVAL_SET).read_text())
    want = {t["name"]: t["sha256"] for t in reg["new_compositions"]["tasks"] + reg["regression"]["tasks"]}
    if pathlib.Path(PSI_EVAL_SET).exists():
        psi = json.loads(pathlib.Path(PSI_EVAL_SET).read_text())
        want.update({t["name"]: t["sha256"] for g in ("latent_need30", "ordinary12", "fst16") for t in psi[g]})
    for f41 in ("docs/experiments/dev/psi41/phase3_set.json", "docs/experiments/dev/psi41/eval_set.json",
                "docs/experiments/dev/psi42/dev_set.json", "docs/experiments/dev/psi42/eval_set.json",
                "docs/experiments/dev/psi44/eval_set.json"):
        if pathlib.Path(f41).exists():
            d41 = json.loads(pathlib.Path(f41).read_text())
            want.update({t["name"]: t["sha256"] for g in ("fst", "rha", "lr_need12", "lr_ord12", "hrt") for t in d41.get(g, [])})
    if pathlib.Path(PSI40_EVAL_SET).exists():
        p40 = json.loads(pathlib.Path(PSI40_EVAL_SET).read_text())
        want.update({t["name"]: t["sha256"] for g in ("lr_need30", "lr_ord12", "fst16", "rha16") for t in p40[g]})
    return want


def resolve(name):
    """A task by name: one of env_listroutines.tasks(), or a pre-registered new task rebuilt from its name (routine
    ids and integer parameters, or the parameters of a section 39 finite-state transducer) and accepted only if its
    {name, train, test} hash equals the committed one."""
    specs = {s.name: s for s in E.tasks()}
    if name in specs:
        return specs[name]
    if name.startswith("fst("):
        import psi_fst_family
        return checked(psi_fst_family.parse(name), name)
    if name.startswith("hrt("):
        import psi42_hrt_family
        return checked(psi42_hrt_family.parse(name), name)
    if name.startswith("rha("):
        import psi40_rha_family
        return checked(psi40_rha_family.parse(name), name)
    parts = []
    for part in name.split(" | "):
        rid, _, rest = part.partition("(")
        params = {}
        for kv in filter(None, rest.rstrip(")").split(",")):
            k, v = kv.split("=")
            params[k] = int(v)
        if rid not in E.R:
            raise KeyError(name)
        parts.append((rid, params))
    return checked(E.Spec(parts), name)


def checked(spec, name):
    want = registered()
    env = E.Env(spec, 0, budget=60)
    data = {"name": spec.name, "train": [[list(x), list(y) if isinstance(y, tuple) else y] for (x,), y in env._train],
            "test": [list(x) for x in env._test]}
    got = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if spec.name != name or want.get(name) != got:
        raise SystemExit("TASK_HASH_MISMATCH " + name)
    return spec


def job(arm, name, seed_kind, cap, sem):
    ac._inv()
    set_arm(arm)
    spec = resolve(name)
    env = E.Env(spec, 0, budget=60)
    seed = h(name) % 1000 if seed_kind == "base" else (h(name) + 7919 * int(seed_kind)) % 1000
    calls, charges, phase, last = [], [], ["formation"], [None]

    def hook(ev):
        calls.append(ev)
        last[0] = ev
    ac.QUERY_HOOK = hook
    q0 = env.query

    def q(x):
        used = env.used
        y = q0(x)
        if env.used > used:
            ev = last[0] if (phase[0] == "formation" and last[0] is not None and last[0]["x"] == tuple(x)) else None
            charges.append({"phase": phase[0], "category_tag": ev["tag"] if ev else None,
                            "ctx": [list(ev["ctx"][0]), list(ev["ctx"][1])] if ev and ev["ctx"] else None,
                            "direction": ev["direction"] if ev else None, "x": list(x)})
        return y
    env.query = q
    for fname, ph in (("challenge", "challenge"), ("committee_queries", "committee")):
        orig = getattr(ac, fname)

        def wrapped(*a, _orig=orig, _ph=ph, **k):
            prev = phase[0]
            phase[0] = _ph
            try:
                return _orig(*a, **k)
            finally:
                phase[0] = prev
        setattr(ac, fname, wrapped)
    orig_passive = ac.passive

    def passive(*a, **k):
        r = orig_passive(*a, **k)
        phase[0] = "discriminate"        # the only SOURCE use after the passive fallback in run_arm
        return r
    ac.passive = passive
    c0 = time.process_time()
    if arm in ("PDq", "QDq", "RDq", "KDq"):
        # the frozen V2 control: P's SOURCE queries replayed and answered again, solved passively (no formation)
        import os
        src = [json.loads(l) for l in open(os.environ["NEUMANN_REPLAY_ROWS"]) if l.strip()]
        arm_src = {"QDq": "Q", "RDq": "R", "KDq": "K"}.get(arm, "P")   # QDq / RDq / KDq: sections 40 / 41 / 44
        rp = next(r for r in src if r["arm"] == arm_src and r["name"] == name and r["seed_kind"] == seed_kind)
        pred, rec = ac.run_arm("Dq", env, cap, seed=seed, replay=rp["query_inputs"])
    else:
        pred, rec = ac.run_arm("D", env, cap, seed=seed)
    cpu = time.process_time() - c0
    ac.QUERY_HOOK = None
    machines = []
    for m in (rec.get("formation") or {}).get("machines", []):
        ev = m.get("events", [])
        rounds = [e for e in ev if e.startswith("round ")]
        machines.append({
            "direction": m.get("direction"), "events": ev[:60], "W": [c.get("w") for c in m.get("components", [])],
            "conflict_components": sum(1 for c in m.get("components", []) if "inconsistent" in (c.get("why") or "")),
            "updates_synthesised": len(rounds),
            "round0_fold_failures": int(rounds[0].split("failing")[1]) if rounds else None,
            "formed": bool(m.get("formed")), "challenge": m.get("challenge"), "update": m.get("update"),
            "cpu": m.get("cpu"), "queries": m.get("queries_used"), "query_purpose": m.get("query_purpose"),
            "reach": m.get("reach"), "psi": m.get("psi"), "psi40": m.get("psi40"), "repair": m.get("repair"),
            "psi43_first": m.get("psi43_first"), "psi44_first": m.get("psi44_first"),
            "components": [{k: c.get(k) for k in ("w", "kind", "source", "update", "init", "why")}
                           for c in m.get("components", [])]})
    initial = env.initial()
    row = {"arm": arm, "name": name, "seed_kind": seed_kind, "seed": seed, "clock": "process_time", "cap": cap,
           "budget": 60, "solved": bool(pred is not None and env._score(pred)), "via": rec.get("via"),
           "queries": env.used, "cpu": round(cpu, 3),
           "formation_cpu": round(sum(m["cpu"] or 0 for m in machines), 3),
           "formation_queries": sum(1 for c in charges if c["phase"] == "formation"),
           "reach_queries": sum(1 for c in charges if c["category_tag"] == "reach"),
           "query_calls": len(calls), "query_calls_cached": sum(1 for c in calls if c["hit"]),
           "duplicate_charges": len(env.log) - len({tuple(x) for x, _ in env.log}),
           "cost": classify(calls, charges),
           "reachable_transitions_observed": reachable_observed(initial, env.log),
           "machines": machines,
           "query_inputs": [list(x) for x, _ in env.log],
           "log_sha256": hashlib.sha256(json.dumps([[list(x), y if not isinstance(y, tuple) else list(y)]
                                                    for x, y in env.log]).encode()).hexdigest()}
    if sem and row["solved"]:
        row["semantic_random300"] = semantic(spec, pred)
    return row


def run(args):
    import concurrent.futures as cf
    import multiprocessing as mp
    names = sorted(json.loads(pathlib.Path(args.names_file).read_text()))
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {(r["arm"], r["name"], r["seed_kind"]) for r in map(json.loads, out.read_text().splitlines())} \
        if out.exists() else set()
    todo = [(arm, name, sk) for sk in args.seeds.split(",") for name in names for arm in args.arms.split(",")
            if (arm, name, sk) not in done]
    with cf.ProcessPoolExecutor(max_workers=args.workers, mp_context=mp.get_context("spawn"),
                                max_tasks_per_child=1) as ex:
        futs = {ex.submit(job, arm, name, sk, args.cap, args.semantic): (arm, name, sk) for arm, name, sk in todo}
        for fut in cf.as_completed(futs):
            row = fut.result()
            with open(out, "a") as fh:
                fh.write(json.dumps(row, sort_keys=True, default=list) + "\n")
            print(row["arm"], row["name"], row["seed_kind"], "solved", row["solved"], "q", row["queries"],
                  "formation_q", row["formation_queries"], "reach_q", row["reach_queries"], "cpu", row["cpu"],
                  "challenge", [m["challenge"] for m in row["machines"]], flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--names-file", required=True)
    p.add_argument("--arms", default="A,D,E")
    p.add_argument("--seeds", default="base", help="comma list: base (sha256(name) % 1000, as active_dev) or ints")
    p.add_argument("--out", required=True)
    p.add_argument("--cap", type=float, default=30.0)
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--semantic", action="store_true")
    run(p.parse_args())
