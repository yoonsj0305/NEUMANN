from __future__ import annotations

import json
from statistics import median
from time import perf_counter_ns

from neumann1.cached_cost_v046 import execute_v046
from neumann1.cached_cost_v046_dataset import prior_v046_signatures, v046_final_examples
from neumann1.cost_gate_v048 import prechoice_features, run_static_gate
from neumann1.cost_gate_v048_dataset import final_examples
from neumann1.indexed_peeling_v043 import execute_peeling
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer
from neumann1.structural_compression import solve_exact_gauss_jordan, verify_exact_full_system


def run() -> dict[str, object]:
    items = final_examples()
    signatures = {item.example.signature for item in items}
    prior = set(prior_v046_signatures())
    prior.update(item.example.signature for item in v046_final_examples())
    fresh = len(signatures) == len(items) == 128 and signatures.isdisjoint(prior)
    scorer = fit_frozen_v033_scorer()
    groups = {name: [] for name in ("high_degree", "dense", "control")}
    rows = []
    for index, item in enumerate(items):
        example = item.example
        paths = {
            "F1": lambda: execute_peeling(example, frozen_scorer=scorer, indexed=True),
            "F3": lambda: execute_v046(example, frozen_scorer=scorer),
            "gate": lambda: run_static_gate(example, frozen_scorer=scorer),
        }
        samples = {name: [] for name in paths}
        outputs = {}
        names = tuple(paths)
        for rep in range(3):
            order = names[(index + rep) % 3:] + names[:(index + rep) % 3]
            for name in order:
                start = perf_counter_ns()
                result = paths[name]()
                samples[name].append((perf_counter_ns() - start) / 1_000_000)
                if name in outputs and outputs[name] != result:
                    raise AssertionError("nondeterministic output")
                outputs[name] = result
        original, _ = solve_exact_gauss_jordan(example.full_system)
        exact, _ = verify_exact_full_system(example.full_system, original)
        verified = exact and all(result.verified and result.answer == original
                                 for result in outputs.values())
        medians = {name: median(sample) for name, sample in samples.items()}
        ratio = medians["F3"] / medians["F1"]
        robust = "F3" if ratio <= 0.90 else "F1" if ratio >= 1.10 else "neutral"
        features = prechoice_features(example)
        gate = outputs["gate"]
        row = {"verified": verified, "ratio": ratio, "gate_ratio": medians["gate"] / medians["F1"],
               "robust": robust, "route": gate.route, "fallback": gate.fallback,
               "degree_six": 6 in features[2], "nnz": features[1],
               "dimension": features[0], "f1_dimension": outputs["F1"].retained_dimension,
               "f3_dimension": outputs["F3"].retained_dimension}
        groups[item.arm].append(row)
        rows.append(row)

    expected = {"high_degree": 48, "dense": 48, "control": 32}
    complete = all(len(groups[arm]) == count for arm, count in expected.items())
    valid = fresh and complete and all(row["verified"] for row in rows)
    robust_counts = {route: sum(row["robust"] == route for row in rows)
                     for route in ("F1", "F3", "neutral")}
    conflicts = sum(row["robust"] != "neutral" and row["robust"] != row["route"]
                    for row in rows)
    decision = ("INVALID_FAMILY" if not valid else
                "OPPORTUNITY_VISIBLE" if robust_counts["F1"] >= 16
                and robust_counts["F3"] >= 16 and conflicts >= 16 else
                "NO_LEARNED_GATE_JUSTIFIED")
    return {
        "version": "0.0.48", "count": len(rows), "fresh": fresh, "complete": complete,
        "verified": valid, "decision": decision, "robust_counts": robust_counts,
        "static_gate_conflicts": conflicts,
        "static_gate_fallbacks": sum(row["fallback"] for row in rows),
        "arms": {arm: {
            "count": len(arm_rows),
            "verified": all(row["verified"] for row in arm_rows),
            "robust_f1": sum(row["robust"] == "F1" for row in arm_rows),
            "robust_f3": sum(row["robust"] == "F3" for row in arm_rows),
            "neutral": sum(row["robust"] == "neutral" for row in arm_rows),
            "gate_f3": sum(row["route"] == "F3" for row in arm_rows),
            "degree_six": sum(row["degree_six"] for row in arm_rows),
            "median_nnz": median(row["nnz"] for row in arm_rows),
            "median_f3_f1_full_path_ratio": median(row["ratio"] for row in arm_rows),
            "median_gate_f1_full_path_ratio": median(row["gate_ratio"] for row in arm_rows),
            "median_f1_retained_dimension": median(row["f1_dimension"] for row in arm_rows),
            "median_f3_retained_dimension": median(row["f3_dimension"] for row in arm_rows),
        } for arm, arm_rows in groups.items()},
        "boundary": "Synthetic exact n=16 systems, noisy local wall time; no trained model, energy, RAM, or deployment claims.",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
