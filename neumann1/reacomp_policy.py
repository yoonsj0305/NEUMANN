"""Deployable example-fitting policy using reused code, without holdout feedback.

Acceptance means a valid cascade fits supplied examples, NOT that the intended
function has been identified. Caller must independently verify any new inputs.
"""
import time

from neumann1.reacomp_adapter import solve


def solve_examples(examples, *, max_programs=5, timeout_per_solver=8):
    started = time.perf_counter()
    attempts = []
    for arm in ("qwen", "cc"):
        result = solve(arm, examples, max_programs, timeout_per_solver)
        attempts.append({"arm": arm, **result})
        if result["accepted"]:
            return {"status": "EXAMPLES_FIT", "program": result["program"],
                    "selected": arm, "attempts": attempts,
                    "elapsed_seconds": time.perf_counter() - started,
                    "unseen_function_equivalence": "NOT_CERTIFIED"}
    return {"status": "ABSTAIN", "program": None, "attempts": attempts,
            "elapsed_seconds": time.perf_counter() - started,
            "unseen_function_equivalence": "NOT_CERTIFIED"}
