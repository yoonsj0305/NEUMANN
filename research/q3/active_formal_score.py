"""Score the Q3 active formal run by the frozen criteria (docs/experiments/q3_active_formal_freeze.json).

python research/q3/active_formal_score.py <rows.jsonl> <record.json>
"""
import collections, hashlib, json, pathlib, sys
sys.path.insert(0, "research/q3")
import invention_first as first
import active_dev as d

FREEZE = "docs/experiments/q3_active_formal_freeze.json"


def structure(r):
    v = r.get("via") or ""
    if not v.startswith("state:"):
        return None
    m = int(v.split("m=")[1]) if "m=" in v else 1
    if m >= 2:
        return "m>=2"
    return "list-state" if r["out_type"] == "L" else "scalar-state"


def main(rows_path, out):
    fz = json.loads(pathlib.Path(FREEZE).read_text())
    sig = fz.pop("freeze_sha256")
    assert hashlib.sha256(json.dumps(fz, sort_keys=True).encode()).hexdigest() == sig, "FREEZE_MUTATED"
    for f, h in fz["code_sha256"].items():
        assert hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest() == h, "CODE_CHANGED " + f
    rows = [json.loads(l) for l in open(rows_path)]
    by = {}
    for r in rows:
        by.setdefault(r["arm"], {})[r["name"]] = r
    names = sorted(s.name for s in d._specs("formal"))
    assert hashlib.sha256("\n".join(names).encode()).hexdigest() == fz["formal_task_names_sha256"]
    errors = {a: sorted(k for k, r in v.items() if r.get("status") == "error") for a, v in by.items()}

    def solved(a, k):          # adverse completion for errors
        r = by[a].get(k)
        if r is None or r.get("status") == "error":
            return a not in ("D", "E")
        return bool(r["solved"])
    so = {a: {k for k in names if solved(a, k)} for a in by}
    vs = lambda a, b: {"first_only": len(so[a] - so[b]), "second_only": len(so[b] - so[a]),
                       "mcnemar_p": first.mcnemar(len(so[a] - so[b]), len(so[b] - so[a]))}
    dq = vs("D", "Dq")
    d_only = sorted(so["D"] - so["Dq"])
    cls = collections.Counter(structure(by["D"][k]) for k in d_only)
    v1 = (dq["first_only"] - dq["second_only"] >= 10 and dq["mcnemar_p"] < 0.05
          and len([c for c in cls if c]) >= 2)
    latent = [k for k in d_only if structure(by["D"][k]) == "m>=2"]
    v2 = len(latent) >= 5
    ed = vs("E", "D")
    cpu = {a: round(sum(r["cpu_seconds"] for r in v.values()), 1) for a, v in by.items()}
    v3 = (ed["first_only"] >= 5 and ed["mcnemar_p"] < 0.05) or (len(so["E"]) >= len(so["D"]) and cpu["E"] <= 0.7 * cpu["D"])
    rec = {"freeze_sha256": sig, "tasks": len(names), "errors": errors,
           "solved": {a: len(s) for a, s in so.items()}, "cpu_seconds": cpu,
           "queries": {a: sum(r.get("queries", 0) for r in v.values()) for a, v in by.items()},
           "comparisons": {"D_vs_Dq": dq, "D_vs_A": vs("D", "A"), "D_vs_C": vs("D", "C"), "C_vs_B": vs("C", "B"),
                           "B_vs_A": vs("B", "A"), "Dq_vs_C": vs("Dq", "C"), "E_vs_D": ed},
           "D_only_vs_Dq": {k: {"structure": structure(by["D"][k]), "via": by["D"][k]["via"], "program": by["D"][k]["program"]}
                            for k in d_only},
           "Dq_only_vs_D": sorted(so["Dq"] - so["D"]),
           "D_only_structure_classes": dict(cls), "D_latent_m2_only": latent,
           "replay_check": d.replay_check(rows),
           "verdict": {"V1_method_invention": "PASS" if v1 else "FAIL",
                       "V2_latent_state_discovery": "PASS" if v2 else "FAIL",
                       "V3_learned_policy": "PASS" if v3 else "FAIL"}}
    pathlib.Path(out).write_text(json.dumps(rec, indent=1, sort_keys=True))
    print(json.dumps({k: v for k, v in rec.items() if k not in ("D_only_vs_Dq",)}, indent=1))
    for k, v in rec["D_only_vs_Dq"].items():
        print("  D+", k, v["structure"], (v["program"] or "")[:90])


if __name__ == "__main__":
    main(*sys.argv[1:3])
