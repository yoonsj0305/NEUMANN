"""Reuse pinned MIT ReaComp solvers; strictly verify returned replace cascades.

The caller supplies examples only. No gold program, task label, or withheld
example reaches the solver subprocess. No upstream code is changed.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time


VENDOR = Path(__file__).resolve().parents[1] / "interop" / "reacomp"


def verify_vendor() -> dict:
    manifest = json.loads((VENDOR / "manifest.json").read_text(encoding="utf-8"))
    for relative, expected in manifest["files"].items():
        path = (VENDOR / "upstream" / relative).resolve()
        if not path.is_relative_to((VENDOR / "upstream").resolve()):
            raise ValueError("vendor path escapes root")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"upstream source mismatch: {relative}")
    return manifest


def normalize(program, max_programs: int) -> list[list[str]]:
    if not isinstance(program, list) or len(program) > max_programs:
        raise ValueError("invalid cascade length/type")
    pairs = []
    for step in program:
        if isinstance(step, str):
            tree = ast.parse(step, mode="eval").body
            if (not isinstance(tree, ast.Call) or not isinstance(tree.func, ast.Name)
                    or tree.func.id != "replace" or len(tree.args) != 2 or tree.keywords
                    or any(not isinstance(arg, ast.Constant) or type(arg.value) is not str
                           for arg in tree.args)):
                raise ValueError("expected exactly replace(string, string)")
            pair = [arg.value for arg in tree.args]
        elif isinstance(step, (list, tuple)) and len(step) == 2:
            pair = list(step)
        else:
            raise ValueError("invalid replacement step")
        if (any(type(value) is not str for value in pair)
                or not 1 <= len(pair[0]) <= 3 or len(pair[1]) > 3):
            raise ValueError("replacement outside DSL")
        pairs.append(pair)
    return pairs


def exact_check(program: list[list[str]], examples: list[list[str]]) -> dict:
    if not examples:
        raise ValueError("verification requires examples")
    correct = 0
    for source, target in examples:
        for pattern, replacement in program:
            source = source.replace(pattern, replacement)
        correct += source == target
    return {"correct": correct, "total": len(examples), "all_correct": correct == len(examples)}


def solve(arm: str, examples: list[list[str]], max_programs: int, timeout: float) -> dict:
    started = time.perf_counter()
    manifest = verify_vendor()
    if arm not in manifest["solvers"]:
        raise ValueError("unknown solver")
    if type(max_programs) is not int or not 1 <= max_programs <= 20:
        raise ValueError("invalid max_programs")
    if not examples or any(not isinstance(pair, (list, tuple)) or len(pair) != 2
                           or any(type(value) is not str for value in pair) for pair in examples):
        raise ValueError("solver needs nonempty string pairs")
    payload = {"arm": arm, "examples": examples, "max_programs": max_programs}
    env = {**os.environ, "PYTHONHASHSEED": "0", "PYTHONIOENCODING": "utf-8"}
    process = subprocess.Popen([sys.executable, "-X", "utf8", "-m", __name__, "--worker"],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding="utf-8", env=env,
                               cwd=Path(__file__).resolve().parents[1])
    try:
        stdout, stderr = process.communicate(json.dumps(payload), timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        return {"status": "TIMEOUT", "accepted": False,
                "elapsed_seconds": time.perf_counter() - started}
    try:
        if process.returncode:
            raise ValueError(f"solver process exited {process.returncode}: {stderr[-1000:]}")
        raw = json.loads(stdout)
        program = normalize(raw["result"]["program"], max_programs)
        checked = exact_check(program, examples)
        accepted = checked["all_correct"] and raw["upstream_reward"] == 1.0
        result = {"status": "COMPLETE", "accepted": accepted, "program": program,
                  "independent_training_check": checked,
                  "upstream_reward": raw["upstream_reward"],
                  "solver_claimed_success": raw["result"].get("success"),
                  "solver_internal_seconds": raw["solver_internal_seconds"]}
    except (ValueError, KeyError, TypeError, SyntaxError) as error:
        result = {"status": "ERROR", "accepted": False, "error": str(error)}
    return {**result, "elapsed_seconds": time.perf_counter() - started}


def worker() -> None:
    payload = json.load(sys.stdin)
    manifest = verify_vendor()
    root = VENDOR / "upstream"
    sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location("reused_solver", root / manifest["solvers"][payload["arm"]])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    kwargs = {"max_programs": payload["max_programs"]}
    for key in ("max_pred_len", "max_transform_len"):
        if key in inspect.signature(module.solve_pbe).parameters:
            kwargs[key] = 3
    started = time.perf_counter()
    result = module.solve_pbe(payload["examples"], **kwargs)
    internal = time.perf_counter() - started
    pairs = normalize(result["program"], payload["max_programs"])
    from rewards.pbebench import reward
    # Published regex verifier cannot parse an empty cascade. Independent
    # identity verification is recorded explicitly; upstream reward stays zero.
    reward_result = reward([f"replace({a!r},{b!r})" for a, b in pairs], True,
                           {"inputs": [pair[0] for pair in payload["examples"]],
                            "outputs": [pair[1] for pair in payload["examples"]]},
                           max_programs=payload["max_programs"])
    print(json.dumps({"result": result, "solver_internal_seconds": internal,
                      "upstream_reward": reward_result["value"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true", required=True)
    parser.parse_args()
    worker()
