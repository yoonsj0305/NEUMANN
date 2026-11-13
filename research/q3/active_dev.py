"""Active structural discovery on the black-box SOURCE environment (development only).

  run <split> <rows.jsonl> [arms]     split = probe | formal; arms default A,B,C,Dq,D
  runE <split> <rows.jsonl>           arm E: D + discovery policy fitted on D's rows of the OTHER folds
  report <split> <rows.jsonl> <record.json>

Tasks: `env_listroutines.tasks()` (108 single routines, 120 compositions); the split is a salted hash of the
task name (probe ~30 %, formal ~70 %), fixed before any run.  Same initial observation (8 examples), same
query budget (8), same CPU cap (6 s, environment execution included) for every arm.
"""
from __future__ import annotations
import collections, hashlib, json, pathlib, sys
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from multiprocessing import Pool
import env_listroutines as E
from neumann1 import active as ac, invention_core as ic
import invention_first as first

CAP, BUDGET, FOLDS = 30.0, 40, 5
POLICY = {}
REPLAY = {}


def _h(s):
    return int(hashlib.sha256(s.encode()).hexdigest(), 16)


def split_of(name):
    return "probe" if _h("neumann-active-split-v1:" + name) % 10 < 3 else "formal"


def fold_of(name):
    return _h("neumann-active-fold-v1:" + name) % FOLDS


def job(a):
    arm, spec = a
    env = E.Env(spec, 0, budget=BUDGET)
    pol = POLICY.get(fold_of(spec.name)) if arm == "E" else None
    try:
        pred, rec = ac.run_arm(arm, env, CAP, seed=_h(spec.name) % 1000, policy=pol, replay=REPLAY.get(spec.name))
    except Exception as e:                       # recorded, never silently counted
        import traceback
        return {"arm": arm, "name": spec.name, "parts": len(spec.parts), "status": "error", "solved": False,
                "fit": False, "queries": env.used, "cpu_seconds": CAP, "error": "%s: %s" % (type(e).__name__, e),
                "trace": traceback.format_exc()[-1500:], "out_type": ac._type(env.initial()[0][1])}
    rec.update(name=spec.name, parts=len(spec.parts), solved=bool(pred is not None and env._score(pred)),
               out_type=ac._type(env.initial()[0][1]), log=[[list(x), y if not isinstance(y, tuple) else list(y)]
                                                           for x, y in env.log])
    f = rec.get("formation")
    if f:
        for h in f.get("hypotheses", {}).values():
            h.pop("ast", None) if h.get("ast") is None else h.update(ast=h["ast"])
    return rec


def _specs(split):
    return [s for s in E.tasks() if split_of(s.name) == split]


def _go(jobs, out):
    done = set()
    try:
        done = {(r["arm"], r["name"]) for r in map(json.loads, open(out))}
    except FileNotFoundError:
        pass
    jobs = [j for j in jobs if (j[0], j[1].name) not in done]
    print("todo", len(jobs), flush=True)
    with Pool(4) as p, open(out, "a") as fh:
        for r in p.imap_unordered(job, jobs, chunksize=1):
            fh.write(json.dumps(r, default=list) + "\n")
            fh.flush()


def run(split, out, arms="A,B,C,Dq,D"):
    _go([(a, s) for a in arms.split(",") for s in _specs(split)], out)


def policy_from(rows, exclude_fold):
    """What the discovery experience of other tasks says: which hypothesis formed, how to split queries, and the
    generative order of step programs that verified."""
    d = [r for r in rows if r["arm"] == "D" and fold_of(r["name"]) != exclude_fold and r.get("formation")]
    formed = collections.Counter(r["formation"].get("formed") for r in d if r["formation"].get("formed"))
    tried = collections.Counter(k for r in d for k in r["formation"].get("hypotheses", {}))
    rate = {k: (formed.get(k, 0) + 0.5) / (tried.get(k, 0) + 1.0) for k in ("prefix", "suffix")}
    order = tuple(sorted(rate, key=lambda k: -rate[k]))
    share = rate[order[0]] / (rate[order[0]] + rate[order[1]])
    first_n = max(1, min(BUDGET - ac.RESERVE - 1, round(share * (BUDGET - ac.RESERVE))))
    split = {order[0]: first_n, order[1]: BUDGET - ac.RESERVE - first_n}
    progs = []
    for r in d:
        f = r["formation"]
        k = f.get("formed")
        if k and f["hypotheses"][k].get("ast"):
            st = r["out_type"]
            progs.append((ic._tup(f["hypotheses"][k]["ast"]), (st, "I") if k == "prefix" else ("I", st)))
    prior = ic.learn_costs(progs, ac._lib()) if progs else None
    return {"order": order, "split": split, "prior": prior, "rate": rate, "n_programs": len(progs)}


def runDq(split, out):
    """Dq replays, query by query, the inputs D submitted (same environment answers); hash-checked later."""
    rows = [json.loads(l) for l in open(out)]
    for r in rows:
        if r["arm"] == "D":
            REPLAY[r["name"]] = r.get("query_inputs", [])
    _go([("Dq", s) for s in _specs(split) if s.name in REPLAY], out)


def replay_check(rows):
    """D and Dq saw the same queries and answers: compare hashes of the logged (input, output) lists."""
    d = {r["name"]: r for r in rows if r["arm"] == "D"}
    q = {r["name"]: r for r in rows if r["arm"] == "Dq"}
    h = lambda r: hashlib.sha256(json.dumps(r.get("log"), sort_keys=True).encode()).hexdigest()
    same = sum(h(d[k]) == h(q[k]) for k in d if k in q)
    return {"pairs": len([k for k in d if k in q]), "identical_query_answer_logs": same}


def runE(split, out):
    rows = [json.loads(l) for l in open(out)]
    for f in range(FOLDS):
        POLICY[f] = policy_from(rows, f)
        print("fold", f, POLICY[f]["order"], POLICY[f]["split"], {k: round(v, 3) for k, v in POLICY[f]["rate"].items()},
              "programs", POLICY[f]["n_programs"], flush=True)
    _go([("E", s) for s in _specs(split)], out)


def _vs(so, a, b):
    w, l = len(so[a] - so[b]), len(so[b] - so[a])
    return {"first_only": w, "second_only": l, "mcnemar_p": first.mcnemar(w, l)}


def report(split, rows_path, out):
    rows = [json.loads(l) for l in open(rows_path)]
    by = {}
    for r in rows:
        by.setdefault(r["arm"], {})[r["name"]] = r
    n = len(next(iter(by.values())))
    so = {a: {k for k, r in v.items() if r["solved"]} for a, v in by.items()}
    rec = {"split": split, "tasks": n, "arms": {}, "replay_check": replay_check(rows)}
    for a, v in sorted(by.items()):
        rec["arms"][a] = {"solved": len(so[a]), "fit": sum(r["fit"] for r in v.values()),
                          "wrong_fit": sum(r["fit"] and not r["solved"] for r in v.values()),
                          "cpu_seconds": round(sum(r["cpu_seconds"] for r in v.values()), 1),
                          "queries": sum(r["queries"] for r in v.values()),
                          "by_parts": dict(collections.Counter(r["parts"] for r in v.values() if r["solved"]))}
    pairs = [("D", "Dq"), ("D", "C"), ("C", "B"), ("B", "A"), ("D", "A"), ("E", "D"), ("Dq", "C")]
    rec["comparisons"] = {"%s_vs_%s" % (a, b): _vs(so, a, b) for a, b in pairs if a in so and b in so}
    if "D" in by:
        formed = {k: r for k, r in by["D"].items() if r.get("formation", {}).get("formed")}
        rec["D_formed_and_challenged"] = len(formed)
        rec["D_formed"] = len(formed)
        rec["D_formed_solved"] = sum(r["solved"] for r in formed.values())
        rec["D_gain_over_Dq"] = {k: {"via": by["D"][k]["via"], "program": by["D"][k]["program"]}
                                 for k in sorted(so["D"] - so.get("Dq", set()))}
        rec["D_loss_to_Dq"] = sorted(so.get("Dq", set()) - so["D"])
        rec["D_machines"] = {k: {"solved": r["solved"], "via": r["via"], "program": r["program"]}
                             for k, r in sorted(by["D"].items()) if r.get("formation", {}).get("formed")}
        rec["D_latent_components_formed"] = sum(1 for r in by["D"].values() if r.get("formation", {}).get("formed")
                                                and "m=1" not in (r.get("via") or ""))
    pathlib.Path(out).write_text(json.dumps(rec, indent=1, sort_keys=True))
    print(json.dumps({k: v for k, v in rec.items() if k not in ("D_gain_over_Dq",)}, indent=1))
    for k, v in rec.get("D_gain_over_Dq", {}).items():
        print("  D+", k, v["via"], (v["program"] or "")[:70])


if __name__ == "__main__":
    {"run": run, "runDq": runDq, "runE": runE, "report": report}[sys.argv[1]](*sys.argv[2:])
