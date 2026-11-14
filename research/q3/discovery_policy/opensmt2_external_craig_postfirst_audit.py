#!/usr/bin/env python3
"""Independent post-first Craig audit for previously frozen OpenSMT2 12-source C2 stdout.
NOT a model proposal; NOT a proof kernel. Fail closed on parser or symbol uncertainty.
"""
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import z3

SRC_COMMIT = "76ee514d36e0a033a160da5e0a138f6fd83e1bcc"
PRE_REG = "8ae6dc5f9b7127b72bfb7d5875a7501f8f780981"
FIRST_FAILED_RUN = 40446804675
FIRST_REPAIR_RUN = 40446877079
PATHS = [
    "regression_itp/uf_bug.smt2",
    "regression_itp/dec-far2.smt2",
    "regression_itp/bug_mask_ite.smt2",
    "regression_itp/itp_bug_small.smt2",
    "regression_itp/uf_itp_problem.smt2",
    "regression_itp/distinct_unsat.smt2",
    "regression_itp/uf-itp-edge-split.smt2",
    "regression_itp/LIA/lia_itp_split.smt2",
    "regression_itp/trivial-proof-A.smt2",
    "regression_itp/trivial-proof-B.smt2",
    "regression_itp/LIA/issue213_itp.smt2",
    "regression_itp/dec-far1.smt2",
]
ALLOWED = {
    "set-info", "set-option", "set-logic", "declare-fun", "declare-const",
    "declare-sort", "define-fun", "assert", "check-sat", "get-interpolants", "exit"
}

def toks(text):
    ans = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch.isspace():
            i += 1
        elif ch == ";":
            p = text.find("\n", i)
            i = len(text) if p < 0 else p + 1
        elif ch in "()":
            ans.append(ch)
            i += 1
        elif ch == '"':
            j = i + 1
            while j < len(text):
                if text[j] == '"':
                    if j + 1 < len(text) and text[j + 1] == '"':
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            else:
                raise ValueError("unterminated_string")
            ans.append(text[i:j])
            i = j
        elif ch == "|":
            j = text.find("|", i + 1)
            if j < 0:
                raise ValueError("unterminated_quoted_symbol")
            ans.append(text[i:j + 1])
            i = j + 1
        else:
            j = i
            while j < len(text) and not text[j].isspace() and text[j] not in "();":
                j += 1
            if j == i:
                raise ValueError("invalid_character")
            ans.append(text[i:j])
            i = j
    return ans

def sexprs(text):
    ts = toks(text)
    def parse(idx):
        if idx >= len(ts):
            raise ValueError("unexpected_eof")
        t = ts[idx]
        if t == "(":
            x = []
            idx += 1
            while idx < len(ts) and ts[idx] != ")":
                v, idx = parse(idx)
                x.append(v)
            if idx >= len(ts):
                raise ValueError("unbalanced")
            return x, idx + 1
        if t == ")":
            raise ValueError("unexpected_closing")
        return t, idx + 1
    out = []
    k = 0
    while k < len(ts):
        v, k = parse(k)
        out.append(v)
    return out

def smt(tree):
    if isinstance(tree, list):
        return "(" + " ".join(map(smt, tree)) + ")"
    return str(tree)

def declared_syms(tree, known):
    found = set()
    def visit(v):
        if isinstance(v, list):
            if v and v[0] in ("let", "forall", "exists", "match"):
                raise ValueError("symbol_scope_requires_full_parser")
            for child in v:
                visit(child)
        elif v in known:
            found.add(v)
    visit(tree)
    return found

def run_z3_script(script):
    # Each Craig obligation runs in a fresh Python process, independent of Java SMTInterpol.
    code = """
import sys, z3
try:
    s=z3.Solver()
    s.set(timeout=3000)
    ast=z3.parse_smt2_string(sys.stdin.read())
    s.add(*ast)
    print(str(s.check()))
except Exception as e:
    print('PARSE_OR_CHECK_ERROR:' + type(e).__name__)
"""
    start = time.monotonic()
    p = subprocess.run(
        [sys.executable, "-c", code], input=script, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=6
    )
    out = p.stdout.strip()
    return {
        "stdout": out,
        "stderr_sha256": hashlib.sha256(p.stderr.encode()).hexdigest(),
        "exit_code": p.returncode,
        "elapsed_seconds": round(time.monotonic() - start, 6),
    }

def check_one(idx, source_root, output_root):
    path = PATHS[idx]
    r = {"index": idx, "path": path, "prereg": PRE_REG,
         "source_commit": SRC_COMMIT, "first_repair_run": FIRST_REPAIR_RUN}
    original_path = source_root / path
    output_path = output_root / "originals" / f"{idx:02d}.stdout"
    if not original_path.is_file() or not output_path.is_file():
        r["status"] = "NOT_RUN_MISSING_ORIGINAL_OR_FROZEN_STDOUT"
        return r
    original = original_path.read_bytes()
    stdout = output_path.read_bytes()
    r["source_git_blob_sha1"] = hashlib.sha1(
        b"blob " + str(len(original)).encode() + bytes([0]) + original
    ).hexdigest()
    r["source_sha256"] = hashlib.sha256(original).hexdigest()
    r["first_stdout_sha256"] = hashlib.sha256(stdout).hexdigest()
    forms = sexprs(original.decode("utf-8"))
    if any(not isinstance(f, list) or not f or f[0] not in ALLOWED for f in forms):
        r["status"] = "HOLD_UNKNOWN_COMMAND_OR_PARSE"
        return r
    checks = [f for f in forms if f[0] == "check-sat"]
    qs = [f for f in forms if f[0] == "get-interpolants"]
    assertions = [f for f in forms if f[0] == "assert"]
    additional_goals = [f for f in forms if f[0] in ("get-proof", "get-model")]
    if len(checks) != 1 or len(qs) != 1 or len(assertions) != 2 or additional_goals:
        r["status"] = "HOLD_OUT_OF_NARROW_SCOPE"
        return r
    if len(qs[0]) != 3 or not all(isinstance(x, str) for x in qs[0][1:]):
        r["status"] = "HOLD_COMPLEX_PARTITION_QUERY"
        return r
    names = []
    expressions = []
    for assertion in assertions:
        if len(assertion) != 2 or not isinstance(assertion[1], list):
            r["status"] = "HOLD_ASSERT_NOT_SIMPLE_NAMED"
            return r
        annotated = assertion[1]
        if len(annotated) != 4 or annotated[0] != "!" or annotated[2] != ":named":
            r["status"] = "HOLD_ANNOTATED_ASSERT_NOT_SUPPORTED"
            return r
        expressions.append(annotated[1])
        names.append(annotated[3])
    if names != qs[0][1:]:
        r["status"] = "HOLD_PARTITION_NAMES_MISMATCH"
        return r
    lines = [l.strip() for l in stdout.decode("utf-8", "replace").splitlines()
             if l.strip() and l.strip() != "success"]
    if not lines or lines[0] != "unsat":
        r["status"] = "HOLD_NO_UNSAT_PREREQUISITE"
        return r
    if any("error" in x.lower() or "unsupported" in x.lower() for x in lines):
        r["status"] = "HOLD_SOLVER_ERROR"
        return r
    output_terms = sexprs("\n".join(lines[1:]))
    if (len(output_terms) != 1 or not isinstance(output_terms[0], list)
            or len(output_terms[0]) != 1):
        r["status"] = "HOLD_MISSING_OR_NONBINARY_OUTPUT"
        return r
    interpolant = output_terms[0][0]
    r["interpolant_sha256"] = hashlib.sha256(smt(interpolant).encode()).hexdigest()
    declarations = [f for f in forms if f[0] in
                    ("declare-fun", "declare-sort", "declare-const", "define-fun")]
    known = {f[1] for f in declarations if len(f) >= 2 and f[0] in ("declare-fun", "declare-const", "define-fun")}
    symbols_A = declared_syms(expressions[0], known)
    symbols_B = declared_syms(expressions[1], known)
    symbols_I = declared_syms(interpolant, known)
    r["shared_declared_symbols"] = sorted(symbols_A & symbols_B)
    r["interpolant_declared_symbols"] = sorted(symbols_I)
    r["shared_vocabulary_pass"] = symbols_I <= (symbols_A & symbols_B)
    if not r["shared_vocabulary_pass"]:
        r["status"] = "HOLD_INTERPOLANT_USES_PRIVATE_SYMBOL"
        return r
    # Reconstruct exact original formulas/declarations from the original SMT-LIB AST,
    # but NEVER use author comments, status tags or an expected interpolant.
    logic = [f for f in forms if f[0] == "set-logic"]
    if len(logic) != 1:
        r["status"] = "HOLD_LOGIC_MISSING"
        return r
    base = "\n".join(map(smt, logic + declarations))
    A, B, I = map(smt, (expressions[0], expressions[1], interpolant))
    a_not_i = base + "\n(assert (and " + A + " (not " + I + ")))\n"
    i_and_b = base + "\n(assert (and " + I + " " + B + "))\n"
    check_A = run_z3_script(a_not_i)
    check_B = run_z3_script(i_and_b)
    r["Z3_A_AND_NOT_I"] = check_A
    r["Z3_I_AND_B"] = check_B
    r["judge"] = "Independent Z3 4.13.3.0 solver verdict, not independent proof kernel"
    r["status"] = "C2_CHECKED_CRAIG_SOLVER_VERDICT" if (
        check_A["stdout"] == "unsat" and check_B["stdout"] == "unsat"
        and check_A["exit_code"] == 0 and check_B["exit_code"] == 0
    ) else "HOLD_CRAIG_OBLIGATIONS_NOT_BOTH_UNSAT"
    return r

def main():
    root = pathlib.Path(os.environ.get("SOURCE_ROOT", "src"))
    frozen = pathlib.Path(os.environ.get("FIRST_ARTIFACT_ROOT", "first_artifact"))
    results = []
    for idx, name in enumerate(PATHS):
        try:
            row = check_one(idx, root, frozen)
        except Exception as e:
            row = {"index":idx, "path":name, "status":"HOLD_CHECKER_EXCEPTION",
                   "exception_type":type(e).__name__,"exception_message":str(e)[:280]}
        results.append(row)
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"],0) + 1
    payload = {
        "scope":"POSTFIRST independent obligation judge of source-index-exposed cross-project originals",
        "source_repo":"aehyvari/OpenSMT2",
        "source_commit":SRC_COMMIT,
        "prereg_commit":PRE_REG,
        "first_failed_run_id":FIRST_FAILED_RUN,
        "first_repair_run_id":FIRST_REPAIR_RUN,
        "judge":"Z3 parser+two fresh solver processes, not a proof object or kernel",
        "neural_weights_trained":False,
        "cross_individual_author_blind":False,
        "G1":"HOLD",
        "Q1_Q7":"OPEN",
        "counts":counts,
        "results":results
    }
    pathlib.Path("receipt").mkdir(exist_ok=True)
    pathlib.Path("receipt/POSTFIRST_INDEPENDENT_CRAIG.json").write_text(json.dumps(payload,ensure_ascii=False,sort_keys=True,indent=2))
    print("COUNTS", json.dumps(counts,sort_keys=True))
    for r in results:
        print("CHECK",r["index"],r["path"],r["status"])
    # Do not fail CI based on scientific failure; publication status is independent of pass/fail.
if __name__ == "__main__":
    main()
