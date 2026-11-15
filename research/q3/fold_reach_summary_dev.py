"""DEVELOPMENT ONLY: summary of the reachable-state diagnosis and the A / B / C comparisons (no new run).

  python research/q3/fold_reach_summary_dev.py --dir docs/experiments/dev/reachable_state
"""
from __future__ import annotations
import argparse
import json
import pathlib


def rows(path):
    p = pathlib.Path(path)
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def diagnosis(d):
    out = {}
    for r in d:
        if r["conflicts_TR"]:
            verdict = "W_INSUFFICIENT (SOURCE-observed state conflict on reachable states)"
        elif r.get("TR_fit") and r.get("TR_fold_errors") == 0:
            verdict = "REPRESENTABLE (fold-correct Update in the existing cell language under fixed W and z)"
        else:
            verdict = "UNRESOLVED (no conflict; no Update found on T+R within the diagnostic cap; no impossibility claimed)"
        divs = [x["first_divergence"] for x in r.get("A_divergences", []) if isinstance(x.get("first_divergence"), dict)
                and "pair_in_T" in x["first_divergence"]]
        out[r["name"]] = {
            "verdict": verdict, "A_fold_errors": r.get("A_fold_errors"), "T_transitions": r["T_transitions"],
            "R_transitions": r["R_transitions"], "R_new_pairs": r["R_new_pairs"],
            "conflict_witness": r["conflicts_TR"][:1], "z_observed": r["z_observed"], "readout_ok": r["readout_ok"],
            "TR_fit": r.get("TR_fit"), "TR_fold_errors": r.get("TR_fold_errors"),
            "TR_fresh_correct": r.get("TR_fresh_correct"),
            "first_divergences": {"total": len(divs),
                                  "pair_outside_T": sum(not v["pair_in_T"] for v in divs),
                                  "element_unseen_in_T": sum(not v["element_in_T"] for v in divs),
                                  "state_longer_than_T": sum(bool(v["state_longer_than_T"]) for v in divs),
                                  "previous_state_correct": sum(bool(v["previous_state_correct"]) for v in divs)},
            "diagnostic_source_queries": r["diagnostic_source_queries"]}
    return out


def replay(f):
    ev = [r for r in f if r["A"]["fold_errors"] is not None and r["C"]["fold_errors"] is not None]
    s = {"tasks": len(f), "fold_evaluable": len(ev)}
    for arm in "ABC":
        s[arm + "_fold_errors_total"] = sum(r[arm]["fold_errors"] for r in ev if r[arm]["fold_errors"] is not None)
        s[arm + "_fold_zero"] = sum(r[arm]["fold_errors"] == 0 for r in ev)
    for arm in "BC":
        s[arm + "_improved_vs_A"] = [r["name"] for r in ev if r[arm]["fold_errors"] is not None
                                     and r[arm]["fold_errors"] < r["A"]["fold_errors"]]
        s[arm + "_worse_vs_A"] = [r["name"] for r in ev if r[arm]["fold_errors"] is not None
                                  and r[arm]["fold_errors"] > r["A"]["fold_errors"]]
    s["A_fit"] = sum(r["A"]["fold_errors"] is not None for r in f)
    s["C_fit"] = sum(r["C"]["fold_errors"] is not None for r in f)
    s["C_candidates_judged"] = {r["name"]: (r["C"].get("search") or {}).get("tested") for r in f}
    s["C_new_update"] = [r["name"] for r in f if (r["C"].get("search") or {}).get("source") == "reach"]
    s["C_first_equals_A"] = sum(bool(r["C"]["first_equals_A"]) for r in f)
    s["per_task"] = {r["name"]: {arm: {"fold": r[arm]["fold_errors"], "R_fit": r[arm].get("R_fit"),
                                       "fresh": r[arm].get("fresh"), "cpu": r[arm]["cpu"]} for arm in "ABC"}
                     for r in f}
    return s


def machine(m):
    by = {}
    for r in m:
        by.setdefault(r["name"], {})[r["arm"]] = r
    arms = sorted({r["arm"] for r in m})
    s = {"tasks": len(by), "arms": arms}
    for a in arms:
        rs = [v[a] for v in by.values() if a in v]
        s[a] = {"solved": sorted(r["name"] for r in rs if r["solved"]),
                "challenge_passed": sorted(r["name"] for r in rs
                                           if any(x["challenge"] is True for x in r["machines"])),
                "machine_formed": sorted(r["name"] for r in rs if any(x["formed"] for x in r["machines"])),
                "cpu_total": round(sum(r["cpu"] for r in rs), 2), "queries_total": sum(r["queries"] for r in rs)}
    for a in arms:
        if a == "A" or "A" not in s:
            continue
        s[a + "_new_solves_vs_A"] = sorted(set(s[a]["solved"]) - set(s["A"]["solved"]))
        s[a + "_lost_vs_A"] = sorted(set(s["A"]["solved"]) - set(s[a]["solved"]))
    return s


def run(args):
    d = pathlib.Path(args.dir)
    out = {"scope": "DEVELOPMENT ONLY -- opened list-routines; no FRESH / FORMAL data; gates unchanged",
           "diagnosis": diagnosis(rows(d / "reachable_diagnosis.jsonl")),
           "fixed_snapshot_ABC": replay(rows(d / "fold_reach_replay.jsonl"))}
    for name in sorted(p.name for p in d.glob("fold_reach_replay_real*.jsonl")):
        out["fixed_snapshot_ABC_" + name[len("fold_reach_replay_"):-6]] = replay(rows(d / name))
    for name in sorted(p.name for p in d.glob("machine_*.jsonl")):
        out[name[:-6]] = machine(rows(d / name))
    (d / "summary.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "diagnosis"}, indent=1, sort_keys=True)[:6000])


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dir", required=True)
    run(p.parse_args())
