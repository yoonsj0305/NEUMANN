from __future__ import annotations

import json
from statistics import median
from time import perf_counter_ns

from neumann1.cached_cost_v046 import execute_v046
from neumann1.cost_gate_v048 import prechoice_features, run_static_gate
from neumann1.indexed_peeling_v043 import execute_peeling
from neumann1.matched_topology_v049_dataset import final_pairs
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer
from neumann1.structural_compression import solve_exact_gauss_jordan, verify_exact_full_system


def _measure(example, index, scorer):
    methods = {
        "F1": lambda: execute_peeling(example, frozen_scorer=scorer, indexed=True),
        "F3": lambda: execute_v046(example, frozen_scorer=scorer),
        "gate": lambda: run_static_gate(example, frozen_scorer=scorer),
    }
    names = tuple(methods)
    times = {name: [] for name in names}
    outputs = {}
    for rep in range(3):
        order = names[(index + rep) % 3:] + names[:(index + rep) % 3]
        for name in order:
            start = perf_counter_ns()
            result = methods[name]()
            times[name].append((perf_counter_ns() - start) / 1_000_000)
            if name in outputs and outputs[name] != result:
                raise AssertionError("nondeterministic output")
            outputs[name] = result
    original, _ = solve_exact_gauss_jordan(example.full_system)
    verified, _ = verify_exact_full_system(example.full_system, original)
    verified = verified and all(result.verified and result.answer == original
                                for result in outputs.values())
    medians = {name: median(times[name]) for name in names}
    ratio = medians["F3"] / medians["F1"]
    return {"verified": verified, "f1_dimension": outputs["F1"].retained_dimension,
            "f3_dimension": outputs["F3"].retained_dimension,
            "ratio": ratio, "gate_ratio": medians["gate"] / medians["F1"],
            "robust": "F3" if ratio <= 0.90 else "F1" if ratio >= 1.10 else "neutral",
            "gate_route": outputs["gate"].route, "fallback": outputs["gate"].fallback,
            "f3_keys": outputs["F3"].block_keys}


def run() -> dict[str, object]:
    pairs = final_pairs()
    scorer = fit_frozen_v033_scorer()
    seen = set()
    rows = []
    for i, pair in enumerate(pairs):
        a, b = pair.recoverable, pair.retained_support
        assert a.signature != b.signature and a.signature not in seen and b.signature not in seen
        seen.update((a.signature, b.signature))
        same_features = prechoice_features(a) == prechoice_features(b)
        positive = _measure(a, 2*i, scorer)
        negative = _measure(b, 2*i+1, scorer)
        target_key = tuple(sorted(pair.targets, key=lambda name: int(name[1:])))
        contrast = (positive["f3_dimension"] + 2 == negative["f3_dimension"]
                    and any(key[1] == target_key for key in positive["f3_keys"])
                    and not any(key[1] == target_key for key in negative["f3_keys"]))
        rows.append({"k": a.core_dimension, "n": a.apparent_dimension,
                     "features_equal": same_features,
                     "verified": positive["verified"] and negative["verified"],
                     "contrast": contrast, "positive": positive, "negative": negative})

    valid = (len(rows) == 96 and len(seen) == 192 and all(row["features_equal"]
             and row["verified"] and row["contrast"] for row in rows))
    reversals = sum(row["positive"]["robust"] == "F3"
                    and row["negative"]["robust"] == "F1" for row in rows)
    mistakes = sum(row["negative"]["robust"] == "F1"
                   and row["negative"]["gate_route"] == "F3" for row in rows)
    decision = ("INVALID_FAMILY" if not valid else
                "OPPORTUNITY_VISIBLE" if reversals >= 16 and mistakes >= 16 else
                "STRUCTURAL_CONTRAST_NO_COST_HEADROOM")
    cells = {}
    for k in (2, 4):
        for n in (16, 32):
            cell = [row for row in rows if row["k"] == k and row["n"] == n]
            cells[f"{k}x{n}"] = {
                "count": len(cell), "matched_verified": all(row["features_equal"] and row["verified"]
                                                        and row["contrast"] for row in cell),
                "median_positive_f3_f1": median(row["positive"]["ratio"] for row in cell),
                "median_negative_f3_f1": median(row["negative"]["ratio"] for row in cell),
                "median_within_pair_ratio_difference": median(row["negative"]["ratio"]
                                                             - row["positive"]["ratio"] for row in cell),
            }
    return {"version": "0.0.49", "pairs": len(rows), "systems": len(seen),
            "verified_matched_contrast": valid, "robust_reversal_pairs": reversals,
            "static_gate_robust_mistakes": mistakes,
            "positive_robust_f3": sum(row["positive"]["robust"] == "F3" for row in rows),
            "negative_robust_f1": sum(row["negative"]["robust"] == "F1" for row in rows),
            "neutral_positive": sum(row["positive"]["robust"] == "neutral" for row in rows),
            "neutral_negative": sum(row["negative"]["robust"] == "neutral" for row in rows),
            "gate_fallbacks": sum(row[side]["fallback"] for row in rows
                                  for side in ("positive", "negative")),
            "cells": cells, "decision": decision,
            "boundary": "Matched synthetic exact systems; local paired wall time only, no trained model."
            }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
