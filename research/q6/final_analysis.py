"""Post-primary scope, complete SOURCE investment, and finite type-class audit."""
from __future__ import annotations
import itertools
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/q6"))
from source_study import OUT, fold, inventory_for
from neumann1 import invention_core as ic, spec_core as sc
from neumann1.q6.transport import substitute, tup
from reference import execute


def main():
    path = OUT / "final_analysis.json"
    if path.exists():
        raise SystemExit("preserve first final analysis")
    first = json.loads((OUT / "result.json").read_text())
    old = json.loads((ROOT / "docs/experiments/results/spec_core_dev_source.json").read_text())["rule"]["S_rows"]
    all_source = sum(r["cpu_seconds"] for r in old.values())
    successful = sum(r["cpu_seconds"] for r in old.values() if r["solved"])
    failed = sum(r["cpu_seconds"] for r in old.values() if not r["solved"])
    receiver = {t["id"]: t for t in json.loads((ROOT.parent / "q6_source_v1_train_cache.json").read_text())}
    audits = []
    for tid in first["compound_attributed_exclusive"]:
        c0 = time.process_time()
        task = receiver[tid]
        task["train"] = [(tup(i), tup(o)) for i, o in task["train"]]
        inventory = inventory_for(fold(tid))
        stages = sc.subtasks(task) + [{"kind": "ast", "in_types": task["in_types"], "out_type": task["out_type"]}]
        stage_counts, fit = {}, []
        for stage in stages:
            types = tuple(stage["in_types"])
            cols = {t: [("v", j) for j, q in enumerate(types) if q == t] for t in ("I", "B", "L")}
            cols["I"] += [("k", k) for k in sorted(set(range(-2, 10)) | set(ic.data_constants(task["train"])))]
            tested = 0
            for kernel in inventory["kernels"]:
                if kernel.out_type != stage["out_type"]:
                    continue
                for args in itertools.product(*(cols[t] for t in kernel.in_types)):
                    candidate = substitute(kernel.ast, len(kernel.in_types), len(types), dict(enumerate(args)))
                    tested += 1
                    sol = stage["kind"], candidate
                    if all(execute(sol, i) == o for i, o in task["train"]):
                        fit.append({"stage": stage["kind"], "kernel_key": kernel.key, "bindings": args})
            stage_counts[stage["kind"]] = tested
        audits.append({"receiver": tid, "all_type_only_stage_application_counts": stage_counts,
                       "total_applications_tested": sum(stage_counts.values()), "TRAIN_fits": fit,
                       "receiver_TEST_read": False, "cpu_seconds": time.process_time() - c0,
                       "scope": "exhaustive finite T fragment/column/constant class only; not arbitrary typed composition or unlimited Q3 discovery"})
    wrong = [r for r in first["grades"] if r["arm"] == "C" and r["independent_fit"] and not r["independent_solved"]]
    source_cost = all_source + first["extraction_and_preparation_cpu_seconds"]
    horizons = {str(n): {a: source_cost + n * first["total_measured_cpu_seconds"][a] / 40
                         for a in ("B", "T", "C", "C-no-map", "BudgetOnly")} for n in (1, 10, 100)}
    r = {"corrected_SOURCE_investment": {"all_125_discovery_cpu_seconds": all_source,
                                         "successful_57_cpu_seconds": successful,
                                         "failed_68_cpu_seconds": failed,
                                         "reason": "Primary donor-only investment/horizon fields omit failed SOURCE discovery. They are incomplete and must not be used for full-cost claims. Original result JSON remains unchanged."},
         "shared_inverse_discovery_investment_cpu_seconds": None,
         "V_original_macro_training_investment_CPU_seconds": None,
         "corrected_measured_SOURCE_inclusive_horizon_scenarios_seconds": horizons,
         "horizon_scope": "accounting-only uniform recurrence, with every historical SOURCE attempt charged once; not actual warm-run measurements. Shared executor investment and OS/queue overhead remain UNKNOWN.",
         "iso_capability_break_even": "NOT_ADMITTED: C and BudgetOnly solve different task sets; energy and full shared setup unmeasured",
         "type_only_complete_audits": audits,
         "failed_C_generalizations": [{"receiver": r["id"], "program": r["program"],
                                        "candidate_correspondence": r.get("candidate_correspondence"),
                                        "via": r.get("via"), "classification": "TRAIN fit does not certify receiver preconditions/generalization"} for r in wrong],
         "failure_diagnosis_boundary": "No-rule/no-fit may be finite preimage coverage or search/policy/budget; not a proof that no correspondence exists. Fit-but-wrong is a verified applicability/generalization failure.",
         "primary_result_unchanged": True}
    path.write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps(r, indent=2))


if __name__ == "__main__":
    main()
