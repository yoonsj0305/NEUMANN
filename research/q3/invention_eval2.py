"""Checkpointed evaluations of the frozen invention core with the exact executor.

Plans (both pre-registered in docs/research/Q3Q6_SECOND_AND_FRESH_PREREG_2026_11_11.md):

  second   The FIRST registry's TARGET families (rule, dc, oeis), the FIRST frozen core, arms, budgets and PASS
           rules, unchanged.  Disclosed as a SECOND evaluation on opened targets: the FIRST run opened these
           bytes and printed rule A 25/125 and A4 34/125 before it was terminated INCOMPLETE.
  fresh    499 OEIS A000 reserve sequences that were registered by blob SHA-1 before the FIRST run and never
           fetched: first exposure.  F1 = the FIRST frozen core (Q3 on sequences).  F2 = a core trained on LISTS
           ONLY (rule SOURCE) evaluated zero-shot on these sequences (Q6 cross-semantic transfer).

  freeze <plan> <wall_cap_s>              pin code, cores, registries and policy (before any run)
  train_lists <bigbench>                  SOURCE-only: lists-only core for plan fresh (reads rule_source only)
  run <plan> <bigbench> <ec> <oeis>       checkpointed run, then score
  score <plan>                            verdicts from the checkpoint (three-valued, see POLICY)

POLICY for rows that are not `ok` (error / timeout / died / not yet run), fixed here, not after seeing results:
they are UNRESOLVED and never silently counted as failures.  Each rule is evaluated twice: under the ADVERSE
completion (unresolved C-type arm = not solved, unresolved rival = solved) and the FAVOURABLE completion (the
reverse).  PASS iff it passes under ADVERSE; FAIL iff it fails under FAVOURABLE; otherwise INCOMPLETE.  With no
unresolved row this is exactly the registered rule.  Budgets are candidate counts (policy P0); `wall_cap_s` is an
operational safety cap only.
"""
from __future__ import annotations
import copy, datetime, hashlib, json, pathlib, sys, time
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from neumann1 import invention_core as ic
import checkpoint_runner as cr
import invention_first as first
import sequence_specialist

CODE = ("neumann1/invention_core.py", "research/q3/checkpoint_runner.py",
        "research/q3/invention_eval2.py", "research/q3/invention_first.py",
        "research/q3/sequence_specialist.py")
FROZEN = first.FROZEN
LISTS_CORE = "docs/experiments/results/invention_core_lists_only_frozen.json"
CANDIDATES = "docs/experiments/second_eval_candidate_registry.json"
FRESH_POOL = "oeis_A000_reserved_unopened"
WORKERS = 4
FIRST_OBSERVED = {"A": 25, "A4": 34}        # rule TARGET, printed by both FIRST launches
C_TYPE = ("C", "C_L", "C_no_inventions", "C_no_learned_prior")


def P(plan, kind):
    return {"freeze": "docs/experiments/invention_%s_freeze.json",
            "rows": "docs/experiments/results/invention_%s_rows.jsonl",
            "manifest": "docs/experiments/results/invention_%s_manifest.json",
            "result": "docs/experiments/results/invention_%s_result.json"}[kind] % plan


def sha_file(p):
    return first.sha256(pathlib.Path(p).read_bytes())


def load_core(path):
    core = json.loads(pathlib.Path(path).read_text())
    sig = core.pop("core_sha256")
    if first.sha256(first.canon(core).encode()) != sig:
        raise SystemExit("CORE_MUTATED " + path)
    return core, sig


# ------------------------------------------------------------------ freeze
def freeze(plan, wall_cap_s):
    reg, rsig = first.load_registry()
    out = {"schema": "neumann.q3q6.eval2-freeze.v1", "plan": plan,
           "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "code_sha256": {p: sha_file(p) for p in CODE},
           "first_registry_sha256": rsig, "frozen_core_sha256": load_core(FROZEN)[1],
           "budgets": {"target": first.N_TARGET, "strong_classical": first.N_STRONG},
           "budget_policy": "P0: candidate counts only", "wall_cap_s": float(wall_cap_s),
           "workers": WORKERS, "unresolved_policy": "adverse/favourable completion, three-valued verdict"}
    if plan == "fresh":
        out["candidate_registry_sha256"] = json.loads(pathlib.Path(CANDIDATES).read_text())["registry_sha256"]
        out["lists_only_core_sha256"] = load_core(LISTS_CORE)[1]
        out["pool"] = FRESH_POOL
    if plan == "second":
        out["integrity_condition"] = {"rule": FIRST_OBSERVED}
    out["freeze_sha256"] = first.sha256(first.canon(out).encode())
    if pathlib.Path(P(plan, "freeze")).exists():
        raise SystemExit("ALREADY_FROZEN " + plan)
    pathlib.Path(P(plan, "freeze")).write_text(json.dumps(out, indent=1, sort_keys=True))
    print("FROZEN", plan, out["freeze_sha256"])


def check_freeze(plan):
    fz = json.loads(pathlib.Path(P(plan, "freeze")).read_text())
    sig = fz.pop("freeze_sha256")
    if first.sha256(first.canon(fz).encode()) != sig:
        raise SystemExit("FREEZE_MUTATED")
    now = {p: sha_file(p) for p in CODE}
    if now != fz["code_sha256"]:
        raise SystemExit("CODE_CHANGED_AFTER_FREEZE " + ", ".join(p for p in CODE if now[p] != fz["code_sha256"][p]))
    if load_core(FROZEN)[1] != fz["frozen_core_sha256"]:
        raise SystemExit("FROZEN_CORE_CHANGED")
    if plan == "fresh" and load_core(LISTS_CORE)[1] != fz["lists_only_core_sha256"]:
        raise SystemExit("LISTS_CORE_CHANGED")
    fz["freeze_sha256"] = sig
    return fz


# ------------------------------------------------------- lists-only core (plan fresh, SOURCE only)
def train_lists(bigbench):
    from multiprocessing import Pool
    reg, rsig = first.load_registry()
    paths = reg["splits"]["rule_source"]
    rb = first.read_blobs(bigbench, paths, reg["rule_blobs"])
    tasks = [first.load_rule(p, rb[p]) for p in paths]
    t0 = time.perf_counter()
    with Pool(WORKERS) as pool:
        core = ic.train(tasks, rounds=first.ROUNDS, budget=first.N_SOURCE, pool=pool,
                        log=lambda m: print(m, flush=True))
    out = {"schema": "neumann.q3q6.invention-core-lists-only.v1", "registry_sha256": rsig,
           "source": "rule_source only (125 list functions); no integer-sequence task",
           "core_code_sha256": sha_file("neumann1/invention_core.py"),
           "spec": core["spec"], "costs": core["costs"], "memory": core["memory"],
           "source_solved": {k: ic.show(v) for k, v in core["solved"].items()},
           "history": core["history"], "train_wall_s": round(time.perf_counter() - t0, 1)}
    out["core_sha256"] = first.sha256(first.canon(out).encode())
    pathlib.Path(LISTS_CORE).write_text(json.dumps(out, indent=0, sort_keys=True))
    print("LISTS-ONLY core %s: %d inventions, %d/%d source solved" % (
        out["core_sha256"], len(core["spec"]), len(core["solved"]), len(tasks)))


# ------------------------------------------------------------------- jobs
def _mem(core):
    return [(ic._tup(a), tuple(i), o) for a, i, o in core["memory"]]


def arms_first(core):
    """Exactly the arms of invention_first.evaluate()."""
    spec, memory, un = [tuple(x) for x in core["spec"]], _mem(core), ic.untrained_costs()
    un_inv = {"*": ic.learn_costs([], ic.library_from_spec(spec))}
    un_inv["*"]["$mem"] = 3
    main = {"A": ((), un, None, first.N_TARGET), "A4": ((), un, None, first.N_STRONG),
            "B": ((), un, memory, first.N_TARGET), "C": (spec, core["costs"], memory, first.N_TARGET)}
    secondary = {"C_no_inventions": ((), core["costs_base_only"], memory, first.N_TARGET),
                 "C_no_learned_prior": (spec, un_inv, memory, first.N_TARGET)}
    return main, secondary


def plan_tasks(plan, bigbench, ec, oeis):
    reg, _ = first.load_registry()
    s = reg["splits"]
    if plan == "second":
        rb = first.read_blobs(bigbench, s["rule_target"], reg["rule_blobs"])
        db = first.read_blobs(ec, [first.DC_FILE], reg["dc_blob"])
        ob = first.read_blobs(oeis, s["oeis_target"], reg["oeis_blobs"])
        return {"rule": [first.load_rule(p, rb[p]) for p in s["rule_target"]],
                "dc": first.load_dc(db[first.DC_FILE]),
                "oeis": [first.load_oeis(p, ob[p]) for p in s["oeis_target"]]}
    cand = json.loads(pathlib.Path(CANDIDATES).read_text())
    blobs = cand["pools"][FRESH_POOL]["blobs"]
    paths = sorted(blobs)
    ob = first.read_blobs(oeis, paths, blobs)
    return {"oeis_reserve": [first.load_oeis(p, ob[p]) for p in paths]}


def plan_arms(plan, fam):
    core, _ = load_core(FROZEN)
    main, secondary = arms_first(core)
    arms = dict(main)
    if plan == "second" and fam == "rule":
        arms.update(secondary)
    if plan == "fresh":
        lc, _ = load_core(LISTS_CORE)
        lspec, lmem = [tuple(x) for x in lc["spec"]], _mem(lc)
        arms["B_L"] = ((), ic.untrained_costs(), lmem, first.N_TARGET)
        arms["C_L"] = (lspec, lc["costs"], lmem, first.N_TARGET)
    return arms


def job(key, task, spec, costs, budget, memory):
    if key[1] == "D":                      # classical sequence specialist (no search)
        pred = sequence_specialist.predict([o for _, o in task["train"]], first.SEQ_TEST)
        return {"solved": pred == [o for _, o in task["test"]], "fit": pred is not None,
                "n_train": len(task["train"]), "n_hidden": len(task["test"])}
    return cr.solve_job(key, task, spec, costs, budget, memory)


def build(plan, fams):
    jobs, manifest = [], {"plan": plan, "families": {}}
    for fam, tasks in fams.items():
        usable = [t for t in tasks if "unsupported" not in t]
        arms = plan_arms(plan, fam)
        manifest["families"][fam] = {
            "tasks": len(tasks), "usable_ids": [t["id"] for t in usable],
            "unsupported": {t["id"]: t["unsupported"] for t in tasks if "unsupported" in t},
            "arms": list(arms) + (["D"] if fam.startswith("oeis") else [])}
        for arm, (spec, costs, memory, budget) in arms.items():
            for t in usable:
                jobs.append(((fam, arm, t["id"]), t, spec, ic.cost_for(costs, t), budget, memory))
        if fam.startswith("oeis"):
            for t in usable:
                jobs.append(((fam, "D", t["id"]), t, (), None, 0, None))
    return jobs, manifest


def run(plan, bigbench, ec, oeis):
    fz = check_freeze(plan)
    jobs, manifest = build(plan, plan_tasks(plan, bigbench, ec, oeis))
    manifest["freeze_sha256"] = fz["freeze_sha256"]
    pathlib.Path(P(plan, "manifest")).write_text(json.dumps(manifest, indent=0, sort_keys=True))
    state = {"n": len(cr.done_keys(P(plan, "rows"))), "t": time.time()}
    print("jobs %d, already done %d" % (len(jobs), state["n"]), flush=True)

    def log(row):
        state["n"] += 1
        if row["status"] != "ok" or state["n"] % 25 == 0:
            print("%s %d/%d %s %s" % (time.strftime("%H:%M:%S", time.gmtime()), state["n"], len(jobs),
                                      row["key"], row["status"]), flush=True)
    cr.run(jobs, P(plan, "rows"), workers=fz["workers"], wall_cap_s=fz["wall_cap_s"], worker=job, log=log)
    score(plan)


# ------------------------------------------------------------------ score
def _cell(row, arm, mode):
    """Row -> FIRST-schema cell; unresolved rows are completed according to `mode`."""
    if row is not None and row["status"] == "ok":
        c = {"fit": bool(row["fit"]), "solved": bool(row["solved"])}
        if arm != "D":
            c.update({"via": row["via"], "candidates": row["candidates"], "seconds": row["cpu_seconds"],
                      "work": row["work"], "program": row["program"], "n_hidden": row["n_hidden"],
                      "inventions": sorted(first.used_inventions(row["ast"], set())) if row["ast"] else []})
        return c, False
    solved = (arm not in C_TYPE) if mode == "adverse" else (arm in C_TYPE)
    c = {"fit": solved, "solved": solved, "unresolved": row["status"] if row else "not_run"}
    if arm != "D":
        c.update({"via": None, "candidates": 0, "seconds": 0.0, "work": 0, "program": None,
                  "n_hidden": None, "inventions": []})
    return c, True


def report(plan, mode):
    manifest = json.loads(pathlib.Path(P(plan, "manifest")).read_text())
    rows = cr.load(P(plan, "rows"))
    rep = {"schema": "neumann.q3q6.invention-eval2.v1", "plan": plan, "completion": mode, "families": {}}
    unresolved = []
    for fam, m in manifest["families"].items():
        frows = {tid: {"unsupported": why} for tid, why in m["unsupported"].items()}
        for tid in m["usable_ids"]:
            frows[tid] = {}
            for arm in m["arms"]:
                cell, un = _cell(rows.get((fam, arm, tid)), arm, mode)
                frows[tid][arm] = cell
                if un:
                    unresolved.append([fam, arm, tid, cell["unresolved"]])
        rep["families"][fam] = {"tasks": m["tasks"], "usable": len(m["usable_ids"]), "rows": frows}
    return rep, unresolved


def p2(rows, c="C", a="A", b="B", rivals=("A", "A4", "B", "D")):
    """The registered P2 rule for one family (same computation as invention_first.summarize)."""
    rows = [r for r in rows if "unsupported" not in r]
    rivals = [x for x in rivals if rows and x in rows[0]]
    n = lambda x: sum(r[x]["solved"] for r in rows)
    excl = [r for r in rows if r[c]["solved"] and not any(r[x]["solved"] for x in rivals)]
    out = {"solved": {x: n(x) for x in sorted({c, a, b, *rivals})}, "exclusive": len(excl),
           "exclusive_inventions": sorted({i for r in excl for i in r[c].get("inventions", [])})}
    for other in (a, b):
        w = sum(r[c]["solved"] and not r[other]["solved"] for r in rows)
        l = sum(r[other]["solved"] and not r[c]["solved"] for r in rows)
        out["vs_" + other] = {"c_only": w, "other_only": l, "mcnemar_p": round(first.mcnemar(w, l), 6)}
    ok = (n(c) > n(a) and n(c) > n(b) and out["vs_" + a]["mcnemar_p"] < 0.05
          and out["vs_" + b]["mcnemar_p"] < 0.05 and len(excl) >= 5)
    out["verdict"] = "PASS" if ok else "FAIL"
    return out


def three(adverse, favourable):
    return "PASS" if adverse == "PASS" else ("FAIL" if favourable != "PASS" else "INCOMPLETE")


def score(plan):
    core, _ = load_core(FROZEN)
    adv, unresolved = report(plan, "adverse")
    fav, _ = report(plan, "favourable")
    result = {"schema": "neumann.q3q6.invention-eval2-result.v1", "plan": plan,
              "freeze_sha256": json.loads(pathlib.Path(P(plan, "freeze")).read_text())["freeze_sha256"],
              "unresolved": unresolved, "families": adv["families"]}
    if plan == "second":
        sa, va = first.summarize(adv, core)
        sf, vf = first.summarize(fav, core)
        result["summary"], result["summary_favourable"] = sa, (sf if unresolved else None)
        result["verdict"] = {k: (three(va[k], vf[k]) if va[k] in ("PASS", "FAIL") else
                                 (va[k] if va[k] == vf[k] else "INCOMPLETE")) for k in va}
        got = {a: sa["rule"][a]["solved"] for a in FIRST_OBSERVED}
        pending = [u for u in unresolved if u[0] == "rule" and u[1] in FIRST_OBSERVED]
        result["integrity"] = {"expected": FIRST_OBSERVED, "observed": got,
                               "status": "PENDING" if pending else ("OK" if got == FIRST_OBSERVED else "VOID")}
        if result["integrity"]["status"] == "VOID":
            result["verdict"] = {k: "VOID" for k in va}
        result["label"] = "SECOND evaluation on targets opened by the INCOMPLETE FIRST run; not FIRST evidence"
    else:
        ra, rf = list(adv["families"]["oeis_reserve"]["rows"].values()), list(fav["families"]["oeis_reserve"]["rows"].values())
        f1a, f1f = p2(ra), p2(rf)
        f2a, f2f = p2(ra, c="C_L", b="B_L", rivals=("A", "A4", "B_L", "D")), p2(rf, c="C_L", b="B_L", rivals=("A", "A4", "B_L", "D"))
        result["summary"] = {"F1_Q3_sequences_frozen_core": f1a, "F2_Q6_lists_only_core_zero_shot": f2a}
        result["verdict"] = {"F1_Q3_sequences_first_exposure": three(f1a["verdict"], f1f["verdict"]),
                             "F2_Q6_cross_semantic_zero_shot": three(f2a["verdict"], f2f["verdict"]),
                             "global_Q1_Q7": "OPEN"}
        result["label"] = "FIRST exposure of 499 registered, never-fetched OEIS A000 reserve sequences"
    pathlib.Path(P(plan, "result")).write_text(json.dumps(result, indent=0, sort_keys=True))
    print(json.dumps({"unresolved": len(unresolved), "verdict": result["verdict"],
                      "integrity": result.get("integrity")}, indent=1))
    return result


if __name__ == "__main__":
    cmd = sys.argv[1]
    {"freeze": freeze, "train_lists": train_lists, "run": run, "score": score}[cmd](*sys.argv[2:])
