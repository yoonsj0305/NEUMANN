"""Model/solver-free planning and analysis contract for the first Q5 slice.

No source generation or route execution lives here. Synthetic fixture metrics
are never experimental evidence. An evaluator must separately freeze sources
and validate original-task witnesses before calling these analysis helpers.
"""
from __future__ import annotations

import math
import random
from collections import Counter
from statistics import median


ROWS = (32, 64, 128, 256)
WIDTHS = (1, 16, 32)
REPLICATES = 4
SEEDS = (100001, 100002)
EXPECTED_RESULT_GZIP = "a73c21e149852013b7db19c0380ddaa36d5c2d6582051008a22942e7309cf47a"
EXPECTED_RESULT_JSON = "d748f70433360ed76ed226f0608a34418af19e0aa9ec3d6aabe9233751995195"
EXPECTED_WEIGHTS = {
    "100001": "c19ad47a4fd310ba469308529ff87134c6ea5de3066ad5750c4af54d658457ea",
    "100002": "20d012c6536cdb4041f6620307b5dbb1c1f3ab56f9438cbff971123a657c3ab5",
}


def protocol():
    """Return a fresh object so a caller cannot mutate the canonical contract."""
    return {
        "schema": "neumann.q5-scaling-contract.v1",
        "status": "CONTRACT_ONLY_NO_NEW_EVIDENCE",
        "rows": list(ROWS), "width_factors": list(WIDTHS),
        "replicates": REPLICATES, "base_cases": 48, "views": 96,
        "seed_base": 103500, "surface_seed_offset": 400000,
        "conditions": [1, 1000], "model_seeds": list(SEEDS),
        "support_factors": [2, 4],
        "expansion_authority": "original_verifier_rejection_only",
        "warmups": 1, "timed_repeats": 3, "budget_s": 5.0,
        "order_seed": 103991, "amortization_queries": 10000,
        "utility_floor": 0.80, "discovery_burden_max": 0.20,
        "null_control_ratio_max": 1.20,
        "largest_wide_ratio_max": 0.80,
        "bootstrap_repeats": 2000, "bootstrap_seed": 103992,
        "slope_familywise_alpha": 0.05, "slope_comparisons": 8,
        "new_fitting": False, "checkpoint_selection": False,
        "holdout_tuning": False, "cache": "disabled",
        "cross_domain_pass": False, "global_q5_closed": False,
    }


def planned_views():
    """Metadata only; does not open or generate any LP."""
    result = []
    index = 0
    for m in ROWS:
        for width in WIDTHS:
            for replicate in range(REPLICATES):
                pair = f"q5_m{m}_w{width}_r{replicate}"
                for surface in (False, True):
                    result.append({
                        "id": pair + ("_surface" if surface else "_base"),
                        "pair_id": pair, "rows": m, "cols": m * width,
                        "width_factor": width, "replicate": replicate,
                        "seed": protocol()["seed_base"] + index,
                        "condition": (1, 1000)[replicate % 2],
                        "surface": surface,
                    })
                index += 1
    return result


def validate_source_metadata(sources):
    expected = planned_views()
    if sources != expected:
        raise ValueError("Q5 frozen source coverage/order/metadata drift")
    counts = Counter((s["rows"], s["width_factor"], s["surface"]) for s in sources)
    if len(counts) != 24 or set(counts.values()) != {REPLICATES}:
        raise ValueError("Q5 cell coverage drift")


def validate_authority(manifest, training_identity):
    """Gate planning on pinned v102 facts; not a substitute for byte replay."""
    if (manifest.get("format") != "neumann.q34-expand4-fresh-eval-v102.archive.v1"
            or manifest.get("frozen_head") != "46af13c3d7d9b1a87f0a0db8511f5972511beb16"
            or manifest.get("rerun") is not False
            or manifest.get("decision") != "Q34_EXPAND4_FRESH_HOLDOUT_PASS_ADVANCE_Q5"
            or manifest.get("advance_q5") is not True
            or manifest.get("gzip_sha256") != EXPECTED_RESULT_GZIP
            or manifest.get("json_sha256") != EXPECTED_RESULT_JSON):
        raise ValueError("Q5 v102 authority identity drift")
    normalized = {str(k): v for k, v in training_identity.items()}
    if len(normalized) != len(training_identity) or set(normalized) != set(EXPECTED_WEIGHTS):
        raise ValueError("Q5 checkpoint seed identity drift")
    for seed, sha in EXPECTED_WEIGHTS.items():
        if normalized[seed].get("weights_sha256") != sha:
            raise ValueError("Q5 frozen checkpoint drift")


def _nonnegative(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"invalid {label}")
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"invalid {label}")
    return float(value)


def charged_cost(*, proposal_ms, post_ms, fit_setup_ms, cold_start_ms, queries=10000):
    """No successful-path-only discount: post includes every retry/fallback.

    cold_start_ms is the measured whole-process startup/loading cost, not zero
    simply because a model was loaded before the warm measurement loop.
    """
    if type(queries) is not int or queries != protocol()["amortization_queries"]:
        raise ValueError("Q5 amortization contract drift")
    proposal = _nonnegative(proposal_ms, "proposal")
    post = _nonnegative(post_ms, "post")
    investment = _nonnegative(fit_setup_ms, "fit/setup") / queries
    startup = _nonnegative(cold_start_ms, "cold startup") / queries
    return {"complete_ms": proposal + post + investment + startup,
            "discovery_ms": proposal + investment + startup,
            "post_ms": post, "investment_ms": investment, "startup_ms": startup}


def cell_gate(*, direct_ms, oracle_ms, discovery_ms, post_ms,
              direct_verified, oracle_verified, candidate_verified,
              all_attempt_costs_charged, width_factor):
    """Analyze aggregate matched cell costs only after witness validation.

    Failed Direct capability yields no speed ratio, even if its short failed
    attempt is cheaper than a successful candidate. A zero-savings oracle also
    cannot produce a positive utility claim.
    """
    if width_factor not in WIDTHS:
        raise ValueError("Q5 unregistered width")
    flags = (direct_verified, oracle_verified, candidate_verified, all_attempt_costs_charged)
    if any(type(x) is not bool for x in flags):
        raise ValueError("Q5 verification/accounting flags must be boolean")
    direct = _nonnegative(direct_ms, "Direct")
    oracle = _nonnegative(oracle_ms, "oracle")
    discovery = _nonnegative(discovery_ms, "discovery")
    post = _nonnegative(post_ms, "post")
    if direct <= 0:
        raise ValueError("Q5 Direct cost must be positive")
    if not all(flags):
        return {"passed": False, "status": "CAPABILITY_OR_ACCOUNTING_UNREACHED",
                "ratio": None, "utility": None, "burden": None}
    ratio = (discovery + post) / direct
    oracle_savings, candidate_savings = direct - oracle, direct - post
    utility = candidate_savings / oracle_savings if oracle_savings > 0 and candidate_savings > 0 else None
    burden = discovery / candidate_savings if candidate_savings > 0 else None
    if width_factor == 1:
        passed = ratio <= protocol()["null_control_ratio_max"]
    else:
        passed = bool(utility is not None and utility >= protocol()["utility_floor"]
                      and burden is not None and burden <= protocol()["discovery_burden_max"]
                      and ratio < 1)
    return {"passed": passed, "status": "PASS" if passed else "COST_GATE_FAIL",
            "ratio": ratio, "utility": utility, "burden": burden}


def log_slope(cost_by_rows):
    if set(cost_by_rows) != set(ROWS):
        raise ValueError("Q5 slope needs every frozen size")
    x = [math.log(m) for m in ROWS]
    y = []
    for m in ROWS:
        value = _nonnegative(cost_by_rows[m], "slope cost")
        if value <= 0:
            raise ValueError("Q5 slope cost must be positive")
        y.append(math.log(value))
    xm, ym = sum(x) / len(x), sum(y) / len(y)
    return sum((a-xm)*(b-ym) for a, b in zip(x, y)) / sum((a-xm)**2 for a in x)


def slope_evidence(paired_costs):
    """Paired cluster bootstrap; no cross-seed/view/width pooling.

    Each size has four (Direct, candidate) median complete costs in frozen
    replicate order. Resample condition-stratified replicate IDs independently
    within each size, preserving the Direct/candidate pairing. A surface view
    is never treated as an independent replicate. The upper bound uses Bonferroni for
    two seeds x two wide factors x two surface statuses.
    """
    if set(paired_costs) != set(ROWS):
        raise ValueError("Q5 slope size coverage drift")
    clean = {}
    for m, pairs in paired_costs.items():
        if len(pairs) != REPLICATES or any(len(p) != 2 for p in pairs):
            raise ValueError("Q5 slope paired replicate coverage drift")
        clean[m] = [tuple(_nonnegative(v, "paired slope cost") for v in p) for p in pairs]
        if any(v <= 0 for p in clean[m] for v in p):
            raise ValueError("Q5 slope paired costs must be positive")

    def slopes(indices):
        direct = {m: median(clean[m][i][0] for i in indices[m]) for m in ROWS}
        candidate = {m: median(clean[m][i][1] for i in indices[m]) for m in ROWS}
        return log_slope(direct), log_slope(candidate)

    direct, candidate = slopes({m: range(REPLICATES) for m in ROWS})
    rng = random.Random(protocol()["bootstrap_seed"])
    differences = []
    for _ in range(protocol()["bootstrap_repeats"]):
        indices = {m: [rng.choice((0, 2)), rng.choice((0, 2)),
                       rng.choice((1, 3)), rng.choice((1, 3))] for m in ROWS}
        d, c = slopes(indices)
        differences.append(c - d)
    differences.sort()
    tail = protocol()["slope_familywise_alpha"] / protocol()["slope_comparisons"]
    upper = differences[min(len(differences)-1, math.ceil((1-tail)*len(differences))-1)]
    return {"direct_slope": direct, "candidate_slope": candidate,
            "slope_difference": candidate-direct, "difference_upper": upper,
            "lower_empirical_slope": upper < 0,
            "cross_domain_pass": False, "global_q5_closed": False}


def summarize_scaling(cell_results, slope_results):
    """Conjunction only: a favorable mean or seed cannot rescue a failed cell.

    Cells are keyed by (seed, m, width, surface); slope groups by
    (seed, width, surface). Callers must separately verify source and witness
    coverage. This function does not certify supplied metrics as evidence.
    """
    expected = {(seed, m, width, surface) for seed in SEEDS for m in ROWS
                for width in WIDTHS for surface in (False, True)}
    if set(cell_results) != expected:
        raise ValueError("Q5 decision cell coverage drift")
    for row in cell_results.values():
        if type(row.get("passed")) is not bool:
            raise ValueError("Q5 cell decision type drift")
    if any(r["status"] == "CAPABILITY_OR_ACCOUNTING_UNREACHED" for r in cell_results.values()):
        decision = "Q5_SCALING_CAPABILITY_OR_ACCOUNTING_UNREACHED"
    elif not all(r["passed"] for r in cell_results.values()):
        decision = "Q5_SCALING_COST_GATE_FAIL"
    elif any(cell_results[seed, 256, width, surface]["ratio"] > protocol()["largest_wide_ratio_max"]
             for seed in SEEDS for width in (16, 32) for surface in (False, True)):
        decision = "Q5_SCALING_COST_GATE_FAIL"
    else:
        required = {(seed, width, surface) for seed in SEEDS
                    for width in (16, 32) for surface in (False, True)}
        if set(slope_results) != required:
            raise ValueError("Q5 decision slope coverage drift")
        for row in slope_results.values():
            upper = row["difference_upper"]
            if isinstance(upper, bool) or not isinstance(upper, (int, float)) or not math.isfinite(upper):
                raise ValueError("Q5 nonfinite slope bound")
            if type(row.get("lower_empirical_slope")) is not bool or row["lower_empirical_slope"] != (upper < 0):
                raise ValueError("Q5 slope decision/bound drift")
        decision = ("Q5_CONSTRUCTED_LP_SCALING_PASS_NOT_CROSS_DOMAIN"
                    if all(r["lower_empirical_slope"] for r in slope_results.values())
                    else "Q5_SCALING_COST_PASS_SLOPE_UNRESOLVED")
    return {"decision": decision, "cross_domain_pass": False, "global_q5_closed": False}
