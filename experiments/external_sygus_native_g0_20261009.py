"""Opened external SyGuS 2019 native-only screening. Not a NEUMANN solver evaluation.

Require exact upstream commit and preregistered task paths.
For solver-produced invariants verify three independent full-quantifier obligations
using Z3, never trusting the external synthesizer's success text alone.
No response-selected or secretly generated training tasks.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/experiments/external_sygus_native_g0_20261009.preregister.json"
DEST = ROOT / "research/development/external_sygus_native_g0_20261009"
CVC5_SECONDS = 15
Z3_MILLISECONDS = 3000


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sexp_parse(string):
    tokens = re.findall(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s()]+', string)
    tokens = [t for t in tokens if not t.startswith(";")]
    stack = [[]]
    for t in tokens:
        if t == "(":
            child = []
            stack[-1].append(child)
            stack.append(child)
        elif t == ")":
            if len(stack) < 2:
                raise ValueError("extra close parenthesis")
            stack.pop()
        else:
            stack[-1].append(t)
    if len(stack) != 1:
        raise ValueError("unclosed parenthesis")
    return stack[0]


def to_smt(e):
    if isinstance(e, list):
        return "(" + " ".join(to_smt(x) for x in e) + ")"
    return str(e)


def find_def(tree, name):
    if isinstance(tree, list):
        if len(tree) >= 2 and tree[0] == "define-fun" and tree[1] == name:
            return tree
        for child in tree:
            result = find_def(child, name)
            if result is not None:
                return result
    return None


def independent_check(source, solution, expected_name="inv-f"):
    """Return 3-valued result and individual obligation states, no guessed proof."""
    import z3

    original = sexp_parse(source)
    candidates = sexp_parse(solution)
    synth = next((x for x in original if isinstance(x, list) and
                  len(x) >= 3 and x[0] == "synth-inv"), None)
    if synth is None or synth[1] != expected_name:
        return {"status": "UNSUPPORTED_SOURCE", "obligations": []}
    inputs = synth[2]
    names = [p[0] for p in inputs]
    if len(set(names)) != len(names):
        return {"status": "INVALID_SOURCE", "obligations": []}
    inv = find_def(candidates, expected_name)
    if inv is None:
        return {"status": "NO_CANDIDATE", "obligations": []}
    if len(inv) != 5 or inv[3] != "Bool" or len(inv[2]) != len(inputs):
        return {"status": "INVALID_CANDIDATE_SIGNATURE", "obligations": []}
    signature = [p[1] for p in inv[2]]
    if signature != [p[1] for p in inputs]:
        return {"status": "INVALID_CANDIDATE_SORTS", "obligations": []}

    base_defs = [x for x in original if isinstance(x, list) and
                 x and x[0] == "define-fun"]
    required = {"pre-f", "trans-f", "post-f"}
    if {x[1] for x in base_defs} != required:
        return {"status": "UNSUPPORTED_DEFINITIONS", "obligations": []}
    defs = "\n".join(to_smt(x) for x in base_defs + [inv]) + "\n"
    cur_args = " ".join(names)
    next_names = [n + "!" for n in names]
    next_args = " ".join(next_names)
    declarations = "".join(f"(declare-const {n} {sort})\n"
                           for n, sort in (inputs + [[n + "!", sort] for n, sort in inputs]))
    goal_queries = [
        f"(and (pre-f {cur_args}) (not ({expected_name} {cur_args})))",
        f"(and ({expected_name} {cur_args}) (trans-f {cur_args} {next_args}) (not ({expected_name} {next_args})))",
        f"(and ({expected_name} {cur_args}) (not (post-f {cur_args})))",
    ]
    obligations = []
    for label, query in zip(("initial", "consecution", "safety"), goal_queries):
        solver = z3.Solver()
        solver.set(timeout=Z3_MILLISECONDS)
        try:
            solver.from_string(defs + declarations + "(assert " + query + ")\n")
            status = str(solver.check())
            obligations.append({"name": label, "smt_result": status,
                                "proved": status == "unsat",
                                "reason_unknown": solver.reason_unknown() if status == "unknown" else None})
        except Exception as exc:
            obligations.append({"name": label, "smt_result": "parse_error",
                                "proved": False, "error": repr(exc)[:600]})
    return {"status": "VERIFIED_ALL_THREE" if all(x["proved"] for x in obligations)
            else "NOT_VERIFIED", "obligations": obligations,
            "candidate_sha256": sha_bytes(to_smt(inv).encode()),
            "candidate_chars": len(to_smt(inv))}


def convert_legacy_sygus(source):
    """SyGuS-IF 2015 declare-primed-var is two declare-var in SyGuS-IF 2.1.
    Parser-only migration. Do not alter any define-fun, invariant or constraint.
    """
    forms = sexp_parse(source)
    converted = []
    decls = 0
    for form in forms:
        if isinstance(form, list) and len(form) == 3 and form[0] == "declare-primed-var":
            _, symbol, sort = form
            converted.extend([["declare-var", symbol, sort],
                              ["declare-var", symbol + "!", sort]])
            decls += 1
        else:
            converted.append(form)
    if decls == 0:
        raise RuntimeError("Expected historic primed declaration absent")
    return "\n".join(to_smt(f) for f in converted) + "\n", decls


def run_screen():
    c = json.loads(CONTRACT.read_text())
    if c["schema"] != "neumann.external-sygus-native-screen.premeasure.v1":
        raise RuntimeError("changed contract schema")
    upstream = ROOT / "third_party/sygus_benchmarks"
    head = subprocess.check_output(["git", "-C", str(upstream),
                                     "rev-parse", "HEAD"], text=True).strip()
    if head != c["upstream"]["sha"]:
        raise RuntimeError(f"external source revision mismatch: {head}")
    solver_version = subprocess.check_output(["cvc5", "--version"], text=True, stderr=subprocess.STDOUT).strip()
    import z3
    records = []
    for path in c["selected_sources"]:
        p = upstream / path
        data = p.read_bytes()
        converted, declaration_count = convert_legacy_sygus(data.decode())
        sandbox = DEST / "converted"
        sandbox.mkdir(parents=True, exist_ok=True)
        effective = sandbox / (str(len(records)) + ".sygus")
        effective.write_text(converted)
        started = time.perf_counter_ns()
        output = ""
        stderr = ""
        exitcode = None
        timeout = False
        try:
            proc = subprocess.run(["cvc5", "--sygus", "--lang=sygus2", str(effective)],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  timeout=CVC5_SECONDS, text=True)
            output, stderr, exitcode = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as e:
            timeout = True
            output = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = (e.stderr or b"").decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        wall_seconds = (time.perf_counter_ns() - started) / 1e9
        result = {"status": "TIMEOUT"} if timeout else (
            independent_check(data.decode(), output) if exitcode == 0 else
            {"status": "SOLVER_ERROR"})
        records.append({
            "source": path, "source_sha256": sha_bytes(data),
            "source_bytes": len(data), "converted_source_sha256": sha_bytes(converted.encode()),
            "legacy_primed_declarations": declaration_count,
            "solver_wall_seconds": wall_seconds,
            "solver_exit_code": exitcode, "solver_timeout": timeout,
            "candidate_result": result, "stdout": output[:50000],
            "stderr": stderr[:5000], "stdout_sha256": sha_bytes(output.encode())})
        print(json.dumps({"source": path, "seconds": round(wall_seconds, 4),
                          "outcome": result["status"], "timeout": timeout}), flush=True)

    counts = {}
    for row in records:
        key = row["candidate_result"]["status"]
        counts[key] = counts.get(key, 0) + 1
    summary = {
        "status": "COMPLETED_OPENED_NATIVE_SCREEN_AFTER_SYNTAX_FIX",
        "technical_attempt_1": "37892764426: 8/8 parser failures, no solver evaluation",
        "originals": len(records), "source_commit": head,
        "contract_sha256": sha_bytes(CONTRACT.read_bytes()),
        "cvc5_version": solver_version, "z3_version": z3.get_version_string(),
        "outcomes": counts, "threads": 1, "solver_timeout_s": CVC5_SECONDS,
        "validator_timeout_ms": Z3_MILLISECONDS,
        "admission": False, "new_neumann_training": False,
        "scientific_note": "Native baseline only. Solved tasks do not imply NEUMANN learned headroom. "
                           "Unsolved/unknown are not proofs of algorithmic weakness."
    }
    DEST.mkdir(parents=True, exist_ok=True)
    payload = {"summary": summary, "records": records}
    (DEST / "first_native_receipts.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    (DEST / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print("NATIVE_SCREEN_SUMMARY=" + json.dumps(summary, sort_keys=True))
    return summary


if __name__ == "__main__":
    try:
        run_screen()
    except Exception as exc:
        DEST.mkdir(parents=True, exist_ok=True)
        (DEST / "fatal.txt").write_text(repr(exc) + "\n")
        raise
