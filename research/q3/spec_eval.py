"""THIRD evaluation: the specification-space core on the TARGET families opened by FIRST/SECOND.

Pre-registration: docs/research/Q3Q6_SPEC_CORE_DESIGN_AND_THIRD_PREREG_2026_11_12.md

  freeze                         pin code, derived-inverse table, registry, caps, arms and rules (before any run)
  run <bigbench> <ec> <oeis>     checkpointed single-attempt run, then score
  score                          verdicts from the checkpoint (three-valued for unresolved rows)

No file of the FRESH reserve (499 OEIS A000) or of the A001 pool is reachable from this script.
SECOND verdicts are not touched: this script writes only spec_third_* files.
"""
from __future__ import annotations
import datetime, json, pathlib, sys
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from neumann1 import spec_core as sc
import checkpoint_runner as cr
import invention_eval2 as ev2
import invention_first as first
import sequence_specialist

CODE = ("neumann1/spec_core.py", "neumann1/invention_core.py", "research/q3/spec_eval.py",
        "research/q3/checkpoint_runner.py", "research/q3/invention_eval2.py", "research/q3/invention_first.py",
        "research/q3/sequence_specialist.py", sc.INVERSES)
CAP_S = 6.0                      # CPU seconds per task for every arm; "A@4" gets 4 x CAP_S
WALL_CAP_S = 900.0               # operational safety cap only
WORKERS = 4
ARMS = {"rule": ["S", "A", "A@4", "S_no_state", "S_no_inverse"],
        "dc": ["S", "A", "A@4", "S_no_state", "S_no_inverse"],
        "oeis": ["S", "A", "A@4", "D"]}
S_TYPE = ("S",)                  # arms whose unresolved rows are completed against the claim
MIN_EXCLUSIVE = 5
SECOND_RESULT = "docs/experiments/results/invention_second_result.json"
INV = None


def P(kind):
    return {"freeze": "docs/experiments/spec_third_freeze.json",
            "rows": "docs/experiments/results/spec_third_rows.jsonl",
            "manifest": "docs/experiments/results/spec_third_manifest.json",
            "result": "docs/experiments/results/spec_third_result.json"}[kind]


def freeze():
    _, rsig = first.load_registry()
    out = {"schema": "neumann.q3q6.spec-third-freeze.v1",
           "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "code_sha256": {p: ev2.sha_file(p) for p in CODE}, "first_registry_sha256": rsig,
           "cap_cpu_seconds": CAP_S, "strong_baseline_cap_multiple": 4, "wall_cap_s": WALL_CAP_S,
           "workers": WORKERS, "arms": ARMS, "min_exclusive": MIN_EXCLUSIVE,
           "rule": "V_f: solved(S) > solved(A) and > solved(A@4); exact two-sided McNemar p < 0.05 vs both; "
                   ">= 5 tasks solved by S and by none of A, A@4 (and D on oeis); total CPU(S) <= total CPU(A). "
                   "Gate = V_rule and V_dc.  Ablations: S > ablation with McNemar p < 0.05, else NOT_SHOWN.",
           "unresolved_policy": "adverse/favourable completion, three-valued verdict",
           "label": "THIRD evaluation on targets opened by FIRST/SECOND; not first-exposure evidence"}
    out["freeze_sha256"] = first.sha256(first.canon(out).encode())
    if pathlib.Path(P("freeze")).exists():
        raise SystemExit("ALREADY_FROZEN")
    pathlib.Path(P("freeze")).write_text(json.dumps(out, indent=1, sort_keys=True))
    print("FROZEN third", out["freeze_sha256"])


def check_freeze():
    fz = json.loads(pathlib.Path(P("freeze")).read_text())
    sig = fz.pop("freeze_sha256")
    if first.sha256(first.canon(fz).encode()) != sig:
        raise SystemExit("FREEZE_MUTATED")
    now = {p: ev2.sha_file(p) for p in CODE}
    if now != fz["code_sha256"]:
        raise SystemExit("CODE_CHANGED_AFTER_FREEZE " + ", ".join(p for p in CODE if now[p] != fz["code_sha256"][p]))
    if (fz["cap_cpu_seconds"], fz["arms"], fz["min_exclusive"]) != (CAP_S, ARMS, MIN_EXCLUSIVE):
        raise SystemExit("POLICY_CHANGED_AFTER_FREEZE")
    fz["freeze_sha256"] = sig
    return fz


def job(key, task, cap):
    global INV
    arm = key[1]
    meta = {"n_train": len(task["train"]), "n_hidden": len(task["test"])}
    if arm == "D":
        pred = sequence_specialist.predict([o for _, o in task["train"]], len(task["test"]))
        return dict(meta, solved=pred == [o for _, o in task["test"]], fit=pred is not None)
    if INV is None:
        INV = sc.load_inverses()
    name, _, k = arm.partition("@")
    r = sc.solve(task, cap * (float(k) if k else 1.0), name, INV)
    r.pop("sol")
    return dict(meta, **r)


def build(fams, cap=CAP_S, arms=ARMS):
    jobs, manifest = [], {"families": {}}
    for fam, tasks in fams.items():
        usable = [t for t in tasks if "unsupported" not in t]
        manifest["families"][fam] = {"tasks": len(tasks), "usable_ids": [t["id"] for t in usable],
                                     "unsupported": {t["id"]: t["unsupported"] for t in tasks if "unsupported" in t},
                                     "arms": arms[fam]}
        for arm in arms[fam]:
            for t in usable:
                jobs.append(((fam, arm, t["id"]), t, cap))
    return jobs, manifest


def run(bigbench, ec, oeis):
    fz = check_freeze()
    jobs, manifest = build(ev2.plan_tasks("second", bigbench, ec, oeis))
    manifest["freeze_sha256"] = fz["freeze_sha256"]
    pathlib.Path(P("manifest")).write_text(json.dumps(manifest, indent=0, sort_keys=True))
    state = {"n": len(cr.done_keys(P("rows")))}
    print("jobs %d, already done %d" % (len(jobs), state["n"]), flush=True)

    def log(row):
        state["n"] += 1
        if row["status"] != "ok" or state["n"] % 50 == 0:
            print("%d/%d %s %s" % (state["n"], len(jobs), row["key"], row["status"]), flush=True)
    cr.run(jobs, P("rows"), workers=fz["workers"], wall_cap_s=fz["wall_cap_s"], worker=job, log=log)
    score()


# ------------------------------------------------------------------- score
def table(mode):
    """{family: {task: {arm: solved}}} with unresolved rows completed per `mode`; plus the unresolved list."""
    manifest = json.loads(pathlib.Path(P("manifest")).read_text())
    rows = cr.load(P("rows"))
    out, unresolved = {}, []
    for fam, m in manifest["families"].items():
        out[fam] = {}
        for tid in m["usable_ids"]:
            cell = {}
            for arm in m["arms"]:
                r = rows.get((fam, arm, tid))
                if r is not None and r["status"] == "ok":
                    cell[arm] = bool(r["solved"])
                else:
                    cell[arm] = (arm not in S_TYPE) if mode == "adverse" else (arm in S_TYPE)
                    unresolved.append([fam, arm, tid, r["status"] if r else "not_run"])
            out[fam][tid] = cell
    return out, unresolved, rows, manifest


def versus(cells, a, b):
    w = sum(c[a] and not c[b] for c in cells)
    l = sum(c[b] and not c[a] for c in cells)
    return {"first_only": w, "second_only": l, "mcnemar_p": round(first.mcnemar(w, l), 6)}


def family_rule(cells, cpu, arms):
    n = {a: sum(c[a] for c in cells) for a in arms}
    rivals = [a for a in ("A", "A@4", "D") if a in arms]
    out = {"solved": n, "S_vs_A": versus(cells, "S", "A"), "S_vs_A@4": versus(cells, "S", "A@4"),
           "exclusive": sum(c["S"] and not any(c[r] for r in rivals) for c in cells),
           "cpu_seconds": cpu, "cpu_S_le_A": cpu["S"] <= cpu["A"]}
    ok = (n["S"] > n["A"] and n["S"] > n["A@4"] and out["S_vs_A"]["mcnemar_p"] < 0.05
          and out["S_vs_A@4"]["mcnemar_p"] < 0.05 and out["exclusive"] >= MIN_EXCLUSIVE and out["cpu_S_le_A"])
    out["verdict"] = "PASS" if ok else "FAIL"
    out["ablations"] = {}
    for ab in ("S_no_state", "S_no_inverse"):
        if ab in arms:
            v = versus(cells, "S", ab)
            v["necessary"] = "SHOWN" if n["S"] > n[ab] and v["mcnemar_p"] < 0.05 else "NOT_SHOWN"
            out["ablations"][ab] = v
    return out


def three(adv, fav):
    return "PASS" if adv == "PASS" else ("FAIL" if fav != "PASS" else "INCOMPLETE")


def score():
    adv, unresolved, rows, manifest = table("adverse")
    fav = table("favourable")[0]
    res = {"schema": "neumann.q3q6.spec-third-result.v1",
           "label": "THIRD evaluation on targets opened by FIRST/SECOND; not first-exposure evidence",
           "freeze_sha256": json.loads(pathlib.Path(P("freeze")).read_text())["freeze_sha256"],
           "unresolved": unresolved, "families": {}, "verdict": {}}
    second = json.loads(pathlib.Path(SECOND_RESULT).read_text())["families"] if pathlib.Path(SECOND_RESULT).exists() else {}
    for fam, m in manifest["families"].items():
        arms = m["arms"]
        ok = lambda a, t: rows.get((fam, a, t)) is not None and rows[(fam, a, t)]["status"] == "ok"
        cpu = {a: round(sum(rows[(fam, a, t)].get("cpu_seconds", 0.0) for t in m["usable_ids"] if ok(a, t)), 1)
               for a in arms}
        fa = family_rule(list(adv[fam].values()), cpu, arms)
        ff = family_rule(list(fav[fam].values()), cpu, arms)
        fa["verdict"] = three(fa["verdict"], ff["verdict"])
        srows = [rows[(fam, "S", t)] for t in m["usable_ids"] if ok("S", t)]
        fa["S_via"] = {}
        for r in srows:
            if r["solved"]:
                fa["S_via"][r["via"]] = fa["S_via"].get(r["via"], 0) + 1
        fa["S_fit"] = sum(r["fit"] for r in srows)
        fa["S_solved_after_80pct_of_cap"] = sum(r["solved"] and r["cpu_seconds"] > 0.8 * CAP_S for r in srows)
        # computation eliminated: S-solved tasks that A@4 could not solve with four times the cap
        gap = sorted(rows[(fam, "S", t)]["cpu_seconds"] for t in m["usable_ids"]
                     if ok("S", t) and ok("A@4", t) and rows[(fam, "S", t)]["solved"] and not rows[(fam, "A@4", t)]["solved"])
        fa["S_cpu_on_tasks_A@4_failed"] = {"n": len(gap), "median": gap[len(gap) // 2] if gap else None,
                                           "max": gap[-1] if gap else None, "A@4_spent_each": 4 * CAP_S}
        both = [(rows[(fam, "S", t)]["cpu_seconds"], rows[(fam, "A", t)]["cpu_seconds"]) for t in m["usable_ids"]
                if ok("S", t) and ok("A", t) and rows[(fam, "S", t)]["solved"] and rows[(fam, "A", t)]["solved"]]
        fa["cpu_on_tasks_both_solve"] = {"n": len(both), "S": round(sum(a for a, _ in both), 2),
                                         "A": round(sum(b for _, b in both), 2)}
        sec = second.get(fam, {}).get("rows", {})
        if sec:                       # reference only: the frozen SECOND arms on the same tasks
            fa["reference_SECOND"] = {a: sum(bool(sec[t].get(a, {}).get("solved")) for t in m["usable_ids"] if t in sec)
                                      for a in ("A", "A4", "B", "C")}
            fa["second_A4_solved_but_A@4_not"] = sum(
                bool(sec[t].get("A4", {}).get("solved")) and not adv[fam][t]["A@4"] for t in m["usable_ids"] if t in sec)
        res["families"][fam] = fa
        res["verdict"]["V_" + fam] = fa["verdict"]
    v = res["verdict"]
    v["THIRD_gate"] = ("PASS" if v.get("V_rule") == "PASS" and v.get("V_dc") == "PASS" else
                       "INCOMPLETE" if "INCOMPLETE" in (v.get("V_rule"), v.get("V_dc")) and "FAIL" not in (v.get("V_rule"), v.get("V_dc"))
                       else "FAIL")
    v["SECOND_verdicts"] = "UNCHANGED (FAIL)"
    v["global_Q1_Q7"] = "OPEN"
    pathlib.Path(P("result")).write_text(json.dumps(res, indent=1, sort_keys=True))
    print(json.dumps({"unresolved": len(unresolved), "verdict": v,
                      "solved": {f: d["solved"] for f, d in res["families"].items()}}, indent=1))
    return res


if __name__ == "__main__":
    {"freeze": freeze, "run": run, "score": score}[sys.argv[1]](*sys.argv[2:])
