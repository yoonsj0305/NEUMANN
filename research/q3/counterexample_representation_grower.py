"""Proof-only supervision -> typed representation refinement from source AST.

TRAIN receives ONLY genuine SAT/UNSAT collision witness rewards from Z3;
not the correct H1 program or operator token. At evaluation the frozen learned
policy predicts whether H0 is insufficient. A generic human-designed AST
binder-lifter builds a new two-array relation when requested, followed by
independent SMT checks of initialization, unbounded induction, nonvacuity,
and deliberately wrong-store SAT counterexample.

This is author-constructed source-free research, not an external-original
solver or autonomously learned universal typed-operator grammar. Direct typed
classical dependency analysis is the stronger equal-rights baseline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/experiments/Q3_COUNTEREXAMPLE_GROWER_FIRST_PREREG_2026_11_06.json"
SCHEMA = "neumann.q3.collision-proof-trained-representation-grower-FIRST.v1"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def ast_size(expr) -> int:
    if not isinstance(expr, list):
        raise ValueError("EXPRESSION_MUST_BE_TYPED_AST")
    return 1 + sum(ast_size(x) for x in expr[1:] if isinstance(x, list))


def count_source_reads(expr) -> int:
    if not isinstance(expr, list) or not expr:
        raise ValueError("BAD_TYPED_AST")
    return int(expr[0] == "select") + sum(count_source_reads(x) for x in expr[1:] if isinstance(x, list))


def expr_term(expr, cursor: str, source: str) -> str:
    """Strict typed term emitter: no target label or prewritten H1 macro."""
    if not isinstance(expr, list) or not expr or not isinstance(expr[0], str):
        raise ValueError("INVALID_AST_NODE")
    op = expr[0]
    if op == "const" and len(expr) == 2 and type(expr[1]) is int:
        return str(expr[1])
    if op == "var" and len(expr) == 2 and expr[1] in ("b", "i"):
        return "b" if expr[1] == "b" else cursor
    if op == "select" and len(expr) == 3 and expr[1] == "S":
        return "(select " + source + " " + expr_term(expr[2], cursor, source) + ")"
    if op in ("add", "mul") and len(expr) == 3:
        left = expr_term(expr[1], cursor, source)
        right = expr_term(expr[2], cursor, source)
        # Exclude general nonlinear arithmetic, which cannot be claimed as
        # AUFLIA proof merely because Z3 accepts a different logic.
        if op == "mul" and not (
            isinstance(expr[1], list) and expr[1][0] == "const"
            or isinstance(expr[2], list) and expr[2][0] == "const"
        ):
            raise ValueError("UNSUPPORTED_NONLINEAR_MULTIPLICATION")
        return "(" + ("+" if op == "add" else "*") + " " + left + " " + right + ")"
    if op == "neg" and len(expr) == 2:
        return "(- " + expr_term(expr[1], cursor, source) + ")"
    raise ValueError("UNKNOWN_TYPED_OPERATOR_" + str(op))


def public_features(expr) -> tuple[float, float, float]:
    expr_term(expr, "i", "S")
    return (1.0, float(count_source_reads(expr)), ast_size(expr) / 12.0)


def task_from(row: dict) -> dict:
    if type(row) is not dict or set(row) != {"expr", "db", "sb"}:
        raise ValueError("EXACT_PUBLIC_TASK_FIELDS_REQUIRED")
    if type(row["db"]) is not int or type(row["sb"]) is not int:
        raise ValueError("INVALID_PUBLIC_TYPED_BASES")
    public_features(row["expr"])
    return row


def common(task: dict) -> str:
    return (
        "(set-logic AUFLIA)\n"
        "(declare-const S (Array Int Int))\n"
        "(declare-const D (Array Int Int))\n"
        "(declare-const S0 (Array Int Int))\n"
        "(declare-const S1 (Array Int Int))\n"
        "(declare-const base Int)\n"
        "(declare-const i Int)\n"
        "(declare-const lim Int)\n"
        "(define-fun a () Int (+ base " + str(task["db"]) + "))\n"
        "(define-fun b () Int (+ base " + str(task["sb"]) + "))\n"
    )


def witness_script(task: dict) -> str:
    """Two source arrays; EXACT SAME D and metadata; different answers."""
    expr = task["expr"]
    good = expr_term(expr, "0", "S0")
    bad = expr_term(expr, "0", "S1")
    return (common(task) +
        "(assert (= (select S0 b) 0))\n"
        "(assert (= (select S1 b) 1))\n"
        "(assert (= (select D a) " + good + "))\n"
        "(assert (not (= (select D a) " + bad + ")))\n"
        "(check-sat)\n"
    )


def relation(task: dict) -> str:
    # GENERIC typed lifting of the actual update AST: substitute i -> j.
    # This is human-written compiler logic, not a model-invented binder.
    rhs = expr_term(task["expr"], "j", "S")
    return (
        "(define-fun NewRel ((S (Array Int Int)) (D (Array Int Int))"
        " (a Int) (b Int) (c Int)) Bool\n"
        " (forall ((j Int)) (=> (and (<= 0 j) (< j c))"
        " (= (select D (+ a j)) " + rhs + "))))\n"
    )


def obligation(task: dict, label: str) -> str:
    source = common(task) + relation(task)
    rhs_now = expr_term(task["expr"], "i", "S")
    if label == "INIT":
        return source + "(assert (not (NewRel S D a b 0)))\n(check-sat)\n"
    if label in ("STEP", "WRONG_STORE"):
        bad = "(+ " + rhs_now + " 1)" if label == "WRONG_STORE" else rhs_now
        return (source +
            "(assert (> lim 0))\n"
            "(assert (<= 0 i))\n"
            "(assert (< i lim))\n"
            "(assert (NewRel S D a b i))\n"
            "(assert (not (NewRel S (store D (+ a i) " + bad
            + ") a b (+ i 1))))\n"
            "(check-sat)\n"
        )
    if label == "NONVACUITY":
        return source + "(assert (NewRel S D a b 1))\n(check-sat)\n"
    raise ValueError("INVALID_ORIGINAL_VERIFICATION_OBLIGATION")


def solver(script: str, limit_s: int = 5) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".smt2", encoding="utf8") as f:
        f.write(script)
        f.flush()
        started = time.perf_counter_ns()
        try:
            p = subprocess.run(
                ["z3", "-smt2", "-T:" + str(limit_s), f.name],
                capture_output=True, text=True, timeout=limit_s + 2, check=False
            )
            answers = [line.strip() for line in p.stdout.splitlines() if line.strip()]
            verdict = (answers[0] if p.returncode == 0 and
                       answers in (["sat"], ["unsat"]) else "UNKNOWN_OR_CHECKER_ERROR")
            stderr = p.stderr[-180:]
        except subprocess.TimeoutExpired:
            verdict = "TIMEOUT_CENSORED_NOT_PROOF"
            stderr = "TIMEOUT"
        return {
            "verdict": verdict, "script_sha256": sha(script.encode()),
            "wall_ms": round((time.perf_counter_ns() - started) / 1e6, 3),
            "stderr_tail": stderr
        }


def certify(task: dict, limit_s: int = 5) -> dict:
    checks = []
    for name, expected in (
        ("INIT", "unsat"), ("STEP", "unsat"),
        ("NONVACUITY", "sat"), ("WRONG_STORE", "sat")
    ):
        out = solver(obligation(task, name), limit_s)
        out.update({"check": name, "expected": expected,
                    "certified": out["verdict"] == expected})
        checks.append(out)
        if not out["certified"]:
            break
    return {
        "full_inductive_proof": len(checks) == 4 and all(x["certified"] for x in checks),
        "independent_verifier_calls": len(checks),
        "verifier_wall_ms": round(sum(x["wall_ms"] for x in checks), 3),
        "relation_program_sha256": sha(relation(task).encode()),
        "has_a_source_ref": count_source_reads(task["expr"]) > 0,
        "checks": checks
    }


def logistic(z: float) -> float:
    return 1 / (1 + math.exp(-max(-100, min(100, z))))


def score(weights: tuple[float, ...], public_ast) -> float:
    features = public_features(public_ast)
    if len(weights) != len(features) or any(not math.isfinite(w) for w in weights):
        raise ValueError("INVALID_LEARNED_POLICY_WEIGHTS")
    return sum(x * w for x, w in zip(features, weights))


def learn(rows: list[dict], oracle_results: list[bool], lr: float, steps: int) -> tuple[float, ...]:
    if len(rows) != len(oracle_results) or len(rows) < 2:
        raise ValueError("UNREGISTERED_LEARNING_DATA")
    w = [0.0, 0.0, 0.0]
    xs = [public_features(row["expr"]) for row in rows]
    for _ in range(steps):
        g = [0.0] * 3
        for x, yes in zip(xs, oracle_results):
            error = logistic(sum(a*b for a, b in zip(x, w))) - float(yes)
            for j in range(3):
                g[j] += error*x[j] / len(rows)
        w = [w[j] - lr*g[j] for j in range(3)]
    return tuple(w)


def evaluate(out: Path) -> dict:
    if not shutil.which("z3"):
        raise RuntimeError("INDEPENDENT_Z3_CLI_REQUIRED")
    m = json.loads(MANIFEST.read_text(encoding="utf8"))
    if m["actual_run"] != "NOT_RUN" or m["train"]["gradient_steps"] != 250:
        raise ValueError("UNFROZEN_FIRST_EXPERIMENT")
    train_rows = [task_from(r) for r in m["train"]["examples"]]
    test_rows = [task_from(r) for r in m["heldout"]["examples"]]
    if len(train_rows) != 6 or len(test_rows) != 8:
        raise ValueError("FIRST_TRAIN_OR_EVAL_DENOMINATOR_CHANGED")
    started = time.perf_counter_ns()
    proofs_train = []
    for row in train_rows:
        output = solver(witness_script(row))
        if output["verdict"] not in ("sat", "unsat"):
            raise RuntimeError("TRAIN_COLLISION_ORACLE_UNKNOWN")
        proofs_train.append(output)
    labels = [o["verdict"] == "sat" for o in proofs_train]
    trained = learn(train_rows, labels, m["train"]["learning_rate"],
                    m["train"]["gradient_steps"])
    checkpoint = {
        "model": "OWN_WEIGHT_THREE_FEATURE_LOGISTIC_POLICY",
        "features": m["train"]["feature_schema"],
        "weights": list(trained), "train_labels_source": "Z3_COLLISION_SAT_OR_UNSAT_ONLY",
        "source_task_bodies_fetched": 0, "external_task_access": False
    }
    checkpoint_raw = (json.dumps(checkpoint, sort_keys=True, separators=(",",":"))+"\n").encode()
    checkpoint_sha = sha(checkpoint_raw)
    frozen = tuple(checkpoint["weights"])
    train_wall = (time.perf_counter_ns() - started) / 1e9
    first_rows = []
    all_z3 = len(proofs_train)
    for row in test_rows:
        # Commit predictions in memory before any target oracle or proof.
        guess = score(frozen, row["expr"]) > 0
        untrained = score((0.0, 0.0, 0.0), row["expr"]) > 0
        classical = count_source_reads(row["expr"]) > 0
        oracle = solver(witness_script(row))
        all_z3 += 1
        if oracle["verdict"] not in ("sat", "unsat"):
            raise RuntimeError("ORIGINAL_HELDOUT_COLLISION_ORACLE_UNKNOWN")
        needs_growth = oracle["verdict"] == "sat"
        student_cert = certify(row) if guess == needs_growth else None
        if student_cert is not None:
            all_z3 += student_cert["independent_verifier_calls"]
        # Charge the stronger deterministic direct source-AST baseline separately.
        classical_cert = certify(row) if classical == needs_growth else None
        if classical_cert is not None:
            all_z3 += classical_cert["independent_verifier_calls"]
        student_verified = (
            guess == needs_growth and student_cert is not None
            and student_cert["full_inductive_proof"]
        )
        classical_verified = (
            classical == needs_growth and classical_cert is not None
            and classical_cert["full_inductive_proof"]
        )
        first_rows.append({
            "heldout_source_AST_sha256": sha(json.dumps(row,sort_keys=True).encode()),
            "source_dependency_oracle_SAT": needs_growth,
            "learned_refine_H0": guess,
            "untrained_zero_refine_H0": untrained,
            "same_rights_classical_typed_dependency_refine_H0": classical,
            "student_correct_refinement": guess == needs_growth,
            "strong_classical_correct_refinement": classical == needs_growth,
            "student_certifies_symbolic_induction": student_verified,
            "strong_classical_certifies_symbolic_induction": classical_verified,
            "student_new_typed_relation_generated_from_source_AST":
                student_cert["relation_program_sha256"] if student_verified else None,
            "model_did_not_receive_human_H1_target_labels": True,
            "H1_semantic_binder_compiler_human_authored": True,
            "collision_verification": oracle,
            "student_verification": student_cert,
            "classical_verification": classical_cert
        })
    correct = sum(r["student_correct_refinement"] for r in first_rows)
    proved = sum(r["student_certifies_symbolic_induction"] for r in first_rows)
    classical_correct = sum(r["strong_classical_correct_refinement"] for r in first_rows)
    classical_proved = sum(r["strong_classical_certifies_symbolic_induction"] for r in first_rows)
    untrained_correct = sum(r["untrained_zero_refine_H0"] == r["source_dependency_oracle_SAT"]
                            for r in first_rows)
    strict = (correct == 8 and proved == 8 and classical_correct == 8 and
              classical_proved == 8 and untrained_correct < correct)
    report = {
        "schema": SCHEMA,
        "scientific_status": ("PASS_SCOPED_COLLISION_TO_TYPED_RELATION" if strict
                              else "FAIL_OR_UNKNOWN_LEARNED_REFINEMENT"),
        "train_example_count": len(train_rows), "heldout_example_count": len(test_rows),
        "train_oracle_collision_labels": [x["verdict"] for x in proofs_train],
        "train_label_information": "BOOLEAN_SAT_UNSAT_ONLY_NO_OPERATOR_ID",
        "learned_checkpoint_sha256": checkpoint_sha, "learned_checkpoint": checkpoint,
        "actual_train_weight_update": max(abs(v) for v in frozen) > 0.01,
        "sourcefree_heldout_correct_policy": correct,
        "sourcefree_heldout_inductively_certified": proved,
        "untrained_policy_correct": untrained_correct,
        "classical_same_rights_correct_policy": classical_correct,
        "classical_same_rights_inductively_certified": classical_proved,
        "learned_additional_solve_over_classical": proved - classical_proved,
        "external_original_CHC_full_proofs": 0,
        "model_automatically_invents_base_grammar": False,
        "compositional_human_typed_binder_lift_not_preauthored_H1_operator": True,
        "symbolic_induction_for_unbounded_index_ranges": True,
        "train_Z3_oracle_calls": len(proofs_train),
        "complete_train_or_eval_Z3_calls": all_z3,
        "actual_train_wall_seconds": round(train_wall,4),
        "complete_experiment_wall_seconds": round((time.perf_counter_ns()-started)/1e9,4),
        "failed_attempts_included": True,
        "Q3":"OPEN","Q4":"OPEN","Q5":"OPEN","Q6":"OPEN","Q7":"OPEN",
        "first_heldout_evidence": first_rows
    }
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    r=evaluate(args.out)
    print(json.dumps({k:v for k,v in r.items() if k not in
        ("learned_checkpoint","first_heldout_evidence")},indent=2,sort_keys=True))
    if r["scientific_status"]!="PASS_SCOPED_COLLISION_TO_TYPED_RELATION":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
