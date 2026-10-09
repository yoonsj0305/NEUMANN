"""Hybrid R0 vertical slice: reuse original solver and independent verifier authority.

Engineering-only. No loaded frozen Q34 model, unseen generalization, GPU claim,
certified optimal rewrite invention, or silent frontier model offload.
"""
from __future__ import annotations

import hashlib
import json
import math
import resource
import sys
from fractions import Fraction
from time import perf_counter_ns
from typing import Any

SCHEMA = "neumann.hybrid-r0-engineering.v0"
DOMAINS = ("lp.standard_form", "exact.linear")
LP_MODES = ("native", "residual_fixed4m", "external_ranking", "frozen_q34")
MAX_INPUT_BYTES = 2_000_000
_FROZEN_Q34_CACHE = None  # Immutable checkpoint reuse within one local process.


def canonical(x: Any) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(x: Any) -> str:
    return hashlib.sha256(canonical(x).encode("utf-8")).hexdigest()


def elapsed_ms(t: int) -> float:
    return (perf_counter_ns() - t) / 1e6


def require_fields(obj: dict, required: set[str], allowed: set[str]) -> None:
    if not isinstance(obj, dict) or not required <= set(obj) or set(obj) - allowed:
        raise ValueError("invalid or missing task fields")


def validate_task(task: Any) -> dict:
    if not isinstance(task, dict):
        raise ValueError("task must be an object")
    kind = task.get("domain")
    if kind not in DOMAINS:
        raise ValueError("domain must be an admitted exact-linear or LP domain")
    if kind == "lp.standard_form":
        require_fields(task, {"domain", "A", "b", "c"},
                       {"domain", "A", "b", "c", "policy", "ranking", "seed", "budget_s"})
        import numpy as np
        a = np.asarray(task["A"], dtype=np.float64)
        b = np.asarray(task["b"], dtype=np.float64)
        c = np.asarray(task["c"], dtype=np.float64)
        if (a.ndim != 2 or not 1 <= a.shape[0] <= 128
                or not a.shape[0] <= a.shape[1] <= 4096
                or b.shape != (a.shape[0],) or c.shape != (a.shape[1],)
                or not all(np.isfinite(x).all() for x in (a, b, c))):
            raise ValueError("LP dimensions or finite coefficients invalid")
        policy = task.get("policy", "native")
        if policy not in LP_MODES:
            raise ValueError("unsupported LP policy")
        if "ranking" in task and policy != "external_ranking":
            raise ValueError("ranking only legal with external_ranking mode")
        if policy == "frozen_q34":
            if type(task.get("seed")) is not int or task["seed"] not in (100001, 100002):
                raise ValueError("frozen_q34 requires one admitted original frozen seed")
        elif "seed" in task:
            raise ValueError("seed only legal for frozen_q34")
        if policy == "external_ranking":
            r = task.get("ranking")
            if (not isinstance(r, list) or len(r) != a.shape[1]
                    or any(type(x) is not int for x in r)
                    or set(r) != set(range(a.shape[1]))):
                raise ValueError("full ranking permutation required")
        budget = task.get("budget_s", 5.0)
        if (type(budget) not in (int, float) or not math.isfinite(budget)
                or not 0 < budget <= 30):
            raise ValueError("finite budget_s in (0,30] required")
        return {"domain": kind, "A": a, "b": b, "c": c,
                "policy": policy, "seed": task.get("seed"),
                "ranking": task.get("ranking"), "budget_s": float(budget)}
    require_fields(task, {"domain", "A", "b"},
                   {"domain", "A", "b", "variables", "budget_s"})
    A, b = task["A"], task["b"]
    if (not isinstance(A, list) or not 1 <= len(A) <= 32
            or not isinstance(b, list) or len(b) != len(A)
            or any(not isinstance(row, list) or len(row) != len(A) for row in A)):
        raise ValueError("exact.linear requires square integer matrix")
    if any(type(v) is not int or abs(v) > 10**9 for row in A for v in row + []) or any(
        type(v) is not int or abs(v) > 10**9 for v in b
    ):
        raise ValueError("exact.linear accepts only bounded JSON integers")
    variables = task.get("variables", [f"x{i}" for i in range(len(A))])
    if (not isinstance(variables, list) or len(variables) != len(A)
            or any(type(x) is not str or not x.isidentifier() or len(x) > 64 for x in variables)
            or len(set(variables)) != len(A)):
        raise ValueError("invalid variable names")
    budget = task.get("budget_s", 5.0)
    if type(budget) not in (int, float) or not math.isfinite(budget) or not 0 < budget <= 30:
        raise ValueError("invalid exact.linear budget")
    return {"domain": kind, "A": A, "b": b, "variables": variables, "budget_s": float(budget)}


def stage_cost(name: str, time_ns: int, stages: dict) -> None:
    stages[name] = stages.get(name, 0.0) + elapsed_ms(time_ns)


def lp_route(spec: dict, stages: dict, events: list, deadline: int) -> tuple[Any, str]:
    from .lp_native_warm_start_v086 import solve_native_checked
    from .lp_q34_support_v097 import adaptive_support_checked
    from .lp_certificate_v081 import verify_standard_form_certificate

    A, b, c = spec["A"], spec["b"], spec["c"]
    m, n = A.shape
    policy = spec["policy"]
    ranking = None
    if policy == "residual_fixed4m":
        from .lp_model_admission_v087 import features
        started = perf_counter_ns()
        _D, _rows, columns = features(A, b, c)
        ranking = __import__("numpy").argsort(columns[:, 1], kind="stable").tolist()
        stage_cost("paid_feature_and_structure_ms", started, stages)
        events.append({"kind": "classical_ranking", "rows": m, "columns": n})
    elif policy == "external_ranking":
        ranking = list(spec["ranking"])
        events.append({"kind": "untrusted_external_ranking", "learned": False,
                       "cost_scope": "external ranking generation UNKNOWN"})
    elif policy == "frozen_q34":
        from experiments.lp_expand4_holdout_v102 import authority_and_models
        from experiments.lp_frozen_support_expansion_v101 import (
            frozen_ranking, investment_per_query,
        )
        global _FROZEN_Q34_CACHE
        load_started = perf_counter_ns()
        was_cached = _FROZEN_Q34_CACHE is not None
        if _FROZEN_Q34_CACHE is None:
            _authority, models, training = authority_and_models()
            _FROZEN_Q34_CACHE = (models, training)
        else:
            models, training = _FROZEN_Q34_CACHE
        stage_cost("frozen_checkpoint_restore_or_cache_lookup_ms", load_started, stages)
        seed = spec["seed"]
        proposal_started = perf_counter_ns()
        ranking, _reported_ms = frozen_ranking({"A": A, "b": b, "c": c}, models[seed])
        stage_cost("frozen_model_proposal_ms", proposal_started, stages)
        events.append({"kind": "frozen_q34_learned_proposal", "seed": seed,
                       "checkpoint_cache_hit": was_cached,
                       "checkpoint_sha256": training[seed]["weights_sha256"],
                       "amortized_training_ms_per_10000_query": investment_per_query(training, seed),
                       "provenance": "v100/v101/v102 historical first archive"})

    remaining = (deadline - perf_counter_ns()) / 1e9
    if remaining <= 0:
        return None, "TIMEOUT"

    started = perf_counter_ns()
    if policy == "native":
        outcome = solve_native_checked(A, b, c, cold_fallback=False, budget_s=remaining)
        candidate = outcome["attempts"][-1]["witness"] if outcome["accepted"] else None
        events.append({"kind": "strong_native", "status": outcome["status"]})
        via = "native"
    else:
        outcome = adaptive_support_checked(A, b, c, ranking,
                                           budget_s=remaining,
                                           factors=(2, 4) if policy == "frozen_q34" else (4,))
        candidate = outcome["witness"] if outcome["accepted"] else None
        events.append({"kind": "certified_restricted_then_native",
                       "subsets_attempted": [x["support_size"] for x in outcome["attempts"]],
                       "fallback": bool(outcome["fallback_used"])})
        via = policy
    stage_cost("native_and_restricted_execution_ms", started, stages)
    if candidate is None:
        return None, "TIMEOUT" if perf_counter_ns() >= deadline else "UNKNOWN"

    started = perf_counter_ns()
    certificate = verify_standard_form_certificate(A, b, c, **candidate)
    stage_cost("independent_original_verification_ms", started, stages)
    events.append({"kind": "independent_original_lp_certificate",
                   "passed": bool(certificate["accepted"])})
    if not certificate["accepted"]:
        return None, "REJECTED"
    if perf_counter_ns() > deadline:
        return None, "TIMEOUT"
    return {"primal": candidate["x"], "dual": candidate["y"],
            "objective": certificate["primal_objective"],
            "method": via, "certificate": certificate["schema"]}, "VERIFIED"


def exact_linear_route(spec: dict, stages: dict, events: list, deadline: int) -> tuple[Any, str]:
    from .structural_compression import ExactLinearSystem, verify_exact_full_system
    from .verified_direct import solve_verified_numeric_or_exact

    system = ExactLinearSystem(variables=tuple(spec["variables"]),
                               A=tuple(tuple(x) for x in spec["A"]),
                               b=tuple(spec["b"]), ground_truth=())
    started = perf_counter_ns()
    try:
        result = solve_verified_numeric_or_exact(system)
    except ValueError:
        stage_cost("exact_or_numeric_execution_ms", started, stages)
        events.append({"kind": "exact_linear_solver", "status": "no_unique_solution"})
        return None, "UNKNOWN"
    stage_cost("exact_or_numeric_execution_ms", started, stages)
    events.append({"kind": "exact_linear_solver",
                   "numeric_then_exact_fallback": result.used_exact_fallback,
                   "proposal_status": result.proposal_status})
    started = perf_counter_ns()
    verified, count = verify_exact_full_system(system, result.answer)
    stage_cost("independent_original_verification_ms", started, stages)
    events.append({"kind": "independent_exact_original_certificate",
                   "passed": bool(verified),
                   "equations": count.equations})
    if not verified:
        return None, "REJECTED"
    if perf_counter_ns() > deadline:
        return None, "TIMEOUT"
    return {"solution": {k: {"numerator": v.numerator, "denominator": v.denominator}
                         for k, v in result.answer.items()},
            "method": "numeric_verified_or_exact_gauss_jordan"}, "VERIFIED"


def run(task: Any) -> dict:
    """Return an original-verified answer, or an explicit non-accepted status.

    Validation can fail; no solver runs on unvalidated inputs. No hidden gold.
    """
    started = perf_counter_ns()
    stages: dict[str, float] = {}
    events: list[dict] = []
    status, answer, reason = "ERROR", None, None
    kind = task.get("domain") if isinstance(task, dict) else None
    task_hash = None
    budget_s = None
    try:
        task_hash = digest(task)
        validation_start = perf_counter_ns()
        spec = validate_task(task)
        stage_cost("input_validation_ms", validation_start, stages)
        budget_s = spec["budget_s"]
        deadline = started + int(budget_s * 1e9)
        if kind == "lp.standard_form":
            answer, status = lp_route(spec, stages, events, deadline)
        else:
            answer, status = exact_linear_route(spec, stages, events, deadline)
    except (TypeError, ValueError, KeyError) as exc:
        reason = f"INVALID_INPUT_OR_DOMAIN_ERROR: {type(exc).__name__}: {exc}"
        status = "ERROR"
        answer = None
    except ImportError as exc:
        reason = f"OPTIONAL_DEPENDENCY_MISSING: {exc}"
        status = "UNKNOWN"
        answer = None
    except Exception as exc:
        reason = f"EXECUTION_ERROR: {type(exc).__name__}: {exc}"
        status = "ERROR"
        answer = None
    total_ms = elapsed_ms(started)
    if budget_s is not None and total_ms > budget_s * 1000:
        status, answer = "TIMEOUT", None
    if status != "VERIFIED":
        answer = None
    stages["unassigned_python_wrapper_ms"] = max(0., total_ms - sum(stages.values()))
    result = {
        "schema": SCHEMA,
        "original_task_sha256": task_hash,
        "domain": kind, "status": status, "answer": answer,
        "reason": reason, "events": events,
        "cost": {
            "observed_wall_ms": total_ms,
            "stages_ms": stages,
            "process_peak_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "model_calls": sum(e.get("kind") == "frozen_q34_learned_proposal"
                               for e in events), "frontier_calls": 0,
            "cold_process_startup_ms": "UNKNOWN",
            "offline_training_investment_ms": (
                next((e["amortized_training_ms_per_10000_query"] for e in events
                      if e.get("kind") == "frozen_q34_learned_proposal"), "UNKNOWN")
            ),
            "external_structure_proposal_ms": "UNKNOWN" if kind == "lp.standard_form" and
                 isinstance(task, dict) and task.get("policy") == "external_ranking" else "NOT_APPLICABLE",
            "measured_energy_j": "UNKNOWN", "cloud_transport_ms": "NOT_APPLICABLE",
        },
        "research_scope": "ENGINEERING_FIXTURE_ONLY_NOT_FRESH_EVIDENCE",
        "learned_model_inference": any(e.get("kind") == "frozen_q34_learned_proposal"
                                       for e in events),
        "north_star_global_questions_closed": [],
    }
    canonical(result)
    return result


def _decode_and_run(raw: bytes) -> dict:
    if len(raw) > MAX_INPUT_BYTES:
        return {"schema": SCHEMA, "status": "ERROR",
                "reason": "INPUT_LIMIT", "answer": None}
    try:
        return run(json.loads(raw.decode("utf-8")))
    except (ValueError, UnicodeError) as exc:
        return {"schema": SCHEMA, "status": "ERROR",
                "reason": f"INVALID_JSON: {type(exc).__name__}", "answer": None}


def main() -> None:
    # Single request by default. --jsonl keeps the frozen archive in one process.
    # Every line is an independent task with independent ORIGINAL certificate.
    if sys.argv[1:] == ["--jsonl"]:
        for line in sys.stdin.buffer:
            print(canonical(_decode_and_run(line)), flush=True)
    elif not sys.argv[1:]:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        print(canonical(_decode_and_run(raw)))
    else:
        print(canonical({"schema": SCHEMA, "status": "ERROR",
                         "reason": "UNSUPPORTED_CLI_ARGUMENT", "answer": None}))


if __name__ == "__main__":
    main()
