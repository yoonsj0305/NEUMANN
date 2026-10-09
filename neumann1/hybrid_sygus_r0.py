"""Source-bound SyGuS loop-invariant adapter for Hybrid R0.

Reuses the three-obligation cvc5 -> independent Z3 semantics from the opened
external SyGuS 2019 native baseline. This is classical-only engineering.
No learned neural proposal or solver-produced result is accepted as proof.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import tempfile
from pathlib import Path
from time import perf_counter_ns

SYM = re.compile(r"^[A-Za-z_][A-Za-z0-9_\-]*$")
TOKENS = re.compile(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s()]+')
VALID_TOP = {"set-logic", "declare-var", "declare-primed-var", "define-fun",
             "synth-inv", "inv-constraint", "check-synth"}


def _ms(stamp):
    return (perf_counter_ns() - stamp) / 1e6


def parse(source: str):
    if not isinstance(source, str) or not source or len(source.encode()) > 40000:
        raise ValueError("missing or oversized SyGuS source")
    tokens = [s for s in TOKENS.findall(source) if not s.startswith(";")]
    if len(tokens) > 10000:
        raise ValueError("SyGuS source token cap")
    stack = [[]]
    for token in tokens:
        if token == "(":
            child = []
            stack[-1].append(child)
            stack.append(child)
            if len(stack) > 128:
                raise ValueError("SyGuS recursion cap")
        elif token == ")":
            if len(stack) <= 1:
                raise ValueError("extra close parenthesis")
            stack.pop()
        else:
            stack[-1].append(token)
    if len(stack) != 1:
        raise ValueError("unclosed SyGuS source")
    return stack[0]


def smt(form):
    return "(" + " ".join(smt(x) for x in form) + ")" if isinstance(form, list) else str(form)


def prepare(source):
    forms = parse(source)
    if not forms or any(not isinstance(f, list) or not f or
                        not isinstance(f[0], str) or f[0] not in VALID_TOP for f in forms):
        raise ValueError("unsupported SyGuS command")
    synth = [f for f in forms if f[0] == "synth-inv"]
    obligations = [f for f in forms if f[0] == "inv-constraint"]
    defs = [f for f in forms if f[0] == "define-fun"]
    if (len(synth) != 1 or len(synth[0]) != 3 or synth[0][1] != "inv-f"
            or len(obligations) != 1 or obligations[0] !=
            ["inv-constraint", "inv-f", "pre-f", "trans-f", "post-f"]
            or {f[1] for f in defs if len(f) > 1} != {"pre-f", "trans-f", "post-f"}
            or len(defs) != 3):
        raise ValueError("unsupported SyGuS invariant structure")
    args = synth[0][2]
    if not isinstance(args, list) or not 1 <= len(args) <= 16:
        raise ValueError("invalid synthesis arguments")
    seen = set()
    for arg in args:
        if (not isinstance(arg, list) or len(arg) != 2
                or not isinstance(arg[0], str) or not SYM.fullmatch(arg[0])
                or arg[0] in seen or arg[1] not in ("Int", "Bool")):
            raise ValueError("unsupported synthesis variable or sort")
        seen.add(arg[0])
    for d in defs:
        if len(d) != 5 or d[3] != "Bool" or not isinstance(d[2], list):
            raise ValueError("unsupported pre/transition/post definition")
    translated = []
    for form in forms:
        if form[0] == "declare-primed-var":
            if (len(form) != 3 or not SYM.fullmatch(form[1])
                    or form[2] not in ("Int", "Bool")):
                raise ValueError("invalid legacy primed variable")
            translated.extend([["declare-var", form[1], form[2]],
                               ["declare-var", form[1] + "!", form[2]]])
        else:
            translated.append(form)
    return "\n".join(smt(x) for x in translated) + "\n", args, defs


def independent_check(original_args, base_defs, output, timeout_ms):
    import z3
    candidate = parse(output)
    # cvc5 emits SyGuS solutions as a parenthesized list of define-fun forms,
    # e.g. ((define-fun inv-f ((x Int)) Bool (>= x 0))).
    # Unwrap exactly one standard solution-list layer; multiple definitions or
    # unrelated output still fail closed. Proof obligations are NOT weakened.
    if (len(candidate) == 1 and isinstance(candidate[0], list)
            and candidate[0] and isinstance(candidate[0][0], list)):
        candidate = candidate[0]
    candidates = [x for x in candidate if isinstance(x, list) and x and x[0] == "define-fun"]
    if len(candidates) != 1:
        return {"accepted": False, "reason": "NO_SINGLE_INVARIANT", "obligations": []}
    inv = candidates[0]
    if (len(inv) != 5 or inv[1] != "inv-f" or inv[3] != "Bool"
            or not isinstance(inv[2], list)
            or len(inv[2]) != len(original_args)
            or [a[1] for a in inv[2]] != [a[1] for a in original_args]):
        return {"accepted": False, "reason": "INVALID_INVARIANT_SIGNATURE", "obligations": []}
    # Function formal parameter names may differ by alpha-renaming.
    # SMT-LIB define-fun binds those names locally. The independently parsed
    # original three proof queries still determine original-task authority.
    names = [p[0] for p in original_args]
    next_names = [n + "!" for n in names]
    curr = " ".join(names)
    next_args = " ".join(next_names)
    declarations = "".join(
        f"(declare-const {name} {sort})\n"
        for name, sort in list(original_args) + [[n + "!", sort] for n, sort in original_args]
    )
    definitions = "\n".join(smt(x) for x in base_defs + [inv]) + "\n"
    queries = [
        f"(and (pre-f {curr}) (not (inv-f {curr})))",
        f"(and (inv-f {curr}) (trans-f {curr} {next_args}) (not (inv-f {next_args})))",
        f"(and (inv-f {curr}) (not (post-f {curr})))",
    ]
    checks = []
    for name, query in zip(("init", "inductive", "safe"), queries):
        s = z3.Solver()
        s.set(timeout=timeout_ms)
        try:
            s.from_string(definitions + declarations + "(assert " + query + ")\n")
            status = str(s.check())
        except Exception as exc:
            status = "parser_error:" + type(exc).__name__
        checks.append({"obligation": name, "smt_result": status,
                       "proved": status == "unsat"})
    return {"accepted": all(v["proved"] for v in checks),
            "obligations": checks,
            "candidate_sha256": hashlib.sha256(smt(inv).encode()).hexdigest(),
            "candidate": smt(inv)}


def solve_and_verify(source: str, budget_s: float, stages: dict, events: list):
    """Solve in cvc5, validate original three obligations in independent Z3."""
    translated, args, defs = prepare(source)
    stages["source_prepare_ms"] = stages.get("source_prepare_ms", 0.0)
    events.append({"kind": "sygus_original_source", "sha256":
                   hashlib.sha256(source.encode()).hexdigest(),
                   "converted_sha256": hashlib.sha256(translated.encode()).hexdigest()})
    with tempfile.TemporaryDirectory(prefix="neumann_r0_sygus_") as folder:
        file = Path(folder) / "input.sy"
        file.write_text(translated)
        stamp = perf_counter_ns()
        try:
            process = subprocess.run(
                ["cvc5", "--sygus", "--lang=sygus2", str(file)],
                text=True, capture_output=True, timeout=budget_s)
        except subprocess.TimeoutExpired:
            stages["sygus_native_ms"] = _ms(stamp)
            events.append({"kind": "sygus_native", "status": "TIMEOUT"})
            return None, "TIMEOUT"
        stages["sygus_native_ms"] = _ms(stamp)
    if process.returncode != 0:
        events.append({"kind": "sygus_native", "status": "ERROR",
                       "stderr_excerpt": process.stderr[:350]})
        return None, "UNKNOWN"
    if len(process.stdout) > 40000:
        events.append({"kind": "sygus_native", "status": "OVERSIZED_ANSWER"})
        return None, "UNKNOWN"
    events.append({"kind": "sygus_native", "status": "CANDIDATE"})
    stamp = perf_counter_ns()
    proof = independent_check(args, defs, process.stdout, timeout_ms=2500)
    stages["independent_original_verification_ms"] = _ms(stamp)
    events.append({"kind": "independent_original_sygus_certificate",
                   "passed": proof["accepted"], "obligations": proof["obligations"],
                   "reason": proof.get("reason"),
                   "candidate_excerpt_on_rejection": process.stdout[:600] if not proof["accepted"] else None})
    if not proof["accepted"]:
        return None, "REJECTED"
    return {"invariant": proof["candidate"],
            "proof_sha256": proof["candidate_sha256"],
            "certificate": "original-sygus-init-consecution-safety-v1"}, "VERIFIED"
