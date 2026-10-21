"""Exact affine-inductive fixed point over an UNCHANGED real SyGuS original.

Zero neural training/forward. Unlike finite observed-source nullspaces, this
CEGIS computes the least affine GF(2) invariant over eligible source Bool state
coordinates. Every proposed closure is checked against the original full Pre
and Trans, and the FINAL induction is checked by native Z3 + independent cvc5.

Mathematical basis: any affine inductive set containing original Pre contains
the initial witness. If it contains the currently observed states, it contains
their affine hull; therefore it contains each original transition successor
from that hull. Every added witness is in every eligible affine invariant.
Finite rank grows strictly on each counterexample (<= n extra additions).
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import time
from pathlib import Path

import z3

from research.evidence.q3_exact_GF2_all_arity_20261021.first_source_64_observation_exact_nullspace import (
    ORIGINS, UPSTREAM, blob, sha, sexprs, compile_typed_original,
    compile_independent_native, dual, nullspace_matrix, sample_pairwise_basis,
    gf2_in_span, add_pivot, independent_original_2vc, candidate_original_native,
    elapsed,
)

FROZEN_FIRST_LEARNED_SHA = "5e9c7f5d1e4039d5a7e3b7edd90857684d8d7ac14b3ab10589b76c2102c2e47b"
TARGET = "lib/Inv_Track/andrew_lustre/DRAGON_2.lus.sl"
QUERY_TIMEOUT_MS = 8000
DUAL_TIMEOUT_S = 12


def row_bits(values):
    return sum((int(b) & 1) << i for i, b in enumerate(values)) | (1 << len(values))


def read_bool_model(model, state, positions):
    return tuple(int(z3.is_true(model.eval(state[i], model_completion=True)))
                 for i in positions)


def query_model(predicate, timeout_ms=QUERY_TIMEOUT_MS):
    solver = z3.Solver()
    solver.set(timeout=timeout_ms, random_seed=0)
    solver.add(predicate)
    ans = solver.check()
    if ans == z3.sat:
        return "sat", solver.model()
    if ans == z3.unsat:
        return "unsat", None
    return "unknown", solver.reason_unknown()


def kernel_expr(basis, states, positions):
    atoms = []
    n = len(positions)
    for v in basis:
        mask = v & ((1 << n) - 1)
        offset = (v >> n) & 1
        terms = [states[positions[i]] for i in range(n) if (mask >> i) & 1]
        if not terms:
            raise RuntimeError("INVALID_TRIVIAL_KERNEL_VECTOR")
        x = z3.BoolVal(False)
        for a in terms:
            x = z3.Xor(x, a)
        atoms.append(x == z3.BoolVal(bool(offset)))
    return z3.And(*atoms) if atoms else z3.BoolVal(True)


def converge(pre, trans, now, nxt, positions, max_ms):
    started = time.perf_counter_ns()
    budget_ns = int(max_ms * 1_000_000)
    outcome, first = query_model(pre)
    if outcome != "sat":
        return {"status": "ABSTAIN_ORIGINAL_INITIAL_NOT_SAT", "pre_outcome": outcome,
                "reason": str(first) if outcome == "unknown" else "VACUOUS_SOURCE_PRE"}

    rows = [read_bool_model(first, now, positions)]
    log = [{"kind": "FIRST_PRE_STATE", "affine_row_rank": 1}]
    n = len(positions)
    terminal = None
    for idx in range(n + 2):
        if time.perf_counter_ns() - started > budget_ns:
            return {"status": "ABSTAIN_WALL_BUDGET", "witness_events": log,
                    "witness_rows_count": len(rows)}
        rank_rows, nullspace = nullspace_matrix(rows, n)
        inv = kernel_expr(nullspace, now, positions)
        inv_next = kernel_expr(nullspace, nxt, positions)
        before = len(rank_rows)

        # First include ALL possible actual source initial states.
        v, data = query_model(z3.And(pre, z3.Not(inv)))
        if v == "unknown":
            return {"status": "ABSTAIN_INITIAL_SMT_UNKNOWN",
                    "reason": str(data), "witness_events": log}
        kind = "ORIGINAL_PRE_CEX"
        witness_vars = now
        if v == "unsat":
            # Then include ALL successors of ANY state in the CURRENT
            # affine hull. This is the key to the least inductive closure.
            v, data = query_model(z3.And(inv, trans, z3.Not(inv_next)))
            if v == "unknown":
                return {"status": "ABSTAIN_TRANS_SMT_UNKNOWN",
                        "reason": str(data), "witness_events": log}
            kind = "ORIGINAL_TRANS_CEX"
            witness_vars = nxt
        if v == "unsat":
            terminal = {"original_Pre_outside_affine_hull": "UNSAT",
                        "original_Trans_successor_outside_affine_hull": "UNSAT"}
            break

        witness = read_bool_model(data, witness_vars, positions)
        if witness in rows:
            raise RuntimeError("COUNTEREXAMPLE_REPEATED_EXISTING_AFFINE_ROW")
        rows.append(witness)
        new_rank = len(nullspace_matrix(rows, n)[0])
        if new_rank != before + 1:
            raise RuntimeError("AFFINE_HULL_RANK_DID_NOT_STRICTLY_INCREASE")
        log.append({"kind": kind, "new_row_rank": new_rank,
                    "previous_row_rank": before, "counterexample_index": idx})
    if terminal is None:
        raise RuntimeError("IMPOSSIBLE_GF2_CEGIS_MORE_THAN_N_PLUS_ONE_RANKS")

    final_rank, final_basis = nullspace_matrix(rows, n)
    return {
        "status": "Z3_EXACT_LEAST_AFFINE_FIXEDPOINT_OBTAINED",
        "iteration_log": log,
        "number_of_independent_source_model_witnesses": len(rows),
        "sampled_state_rows_sha256": sha(json.dumps(rows).encode()),
        "source_witnesses": [list(row) for row in rows],
        "number_of_eligible_source_bool_state_variables": n,
        "GF2_augmented_row_rank": len(final_rank),
        "GF2_complete_inductive_affine_kernel_nullity": len(final_basis),
        "complete_affine_GF2_kernel_vectors": final_basis,
        "terminal_source_global_queries": terminal,
        "witness_rank_strict_increments": all(
            a.get("new_row_rank") == a.get("previous_row_rank", 0) + 1
            for a in log if a["kind"] != "FIRST_PRE_STATE"
        ),
        "z3_search_wall_ms": elapsed(started),
    }


def synthetic_controls():
    # Positive: only even parity states can be reached. The full 4-body
    # relation is real, but no nontrivial 1/2-body relation explains it.
    a = z3.Bools("a0 a1 a2 a3")
    b = z3.Bools("b0 b1 b2 b3")
    def parity(xs):
        result = z3.BoolVal(False)
        for x in xs:
            result = z3.Xor(result, x)
        return result
    positive = converge(z3.And(*[z3.Not(x) for x in a]),
                        parity(a) == parity(b), a, b, list(range(4)), 25000)
    if positive["status"] != "Z3_EXACT_LEAST_AFFINE_FIXEDPOINT_OBTAINED":
        raise RuntimeError("POSITIVE_CONTROL_ABORTED")
    if positive["GF2_complete_inductive_affine_kernel_nullity"] != 1:
        raise RuntimeError("POSITIVE_HIGHER_ORDER_AFFINE_PARITY_MISSED")
    neg = converge(z3.BoolVal(True), z3.BoolVal(True), a, b,
                   list(range(4)), 25000)
    if neg["status"] != "Z3_EXACT_LEAST_AFFINE_FIXEDPOINT_OBTAINED":
        raise RuntimeError("NEGATIVE_CONTROL_ABORTED")
    if neg["GF2_complete_inductive_affine_kernel_nullity"] != 0:
        raise RuntimeError("NEGATIVE_UNCONSTRAINED_SOURCE_FALSE_INVARIANT")
    pair, _ = sample_pairwise_basis(positive["source_witnesses"], 4)
    if len(pair) != 0:
        raise RuntimeError("POSITIVE_HIGHER_ORDER_CONTROL_FAKE_PAIRWISE")
    return {
        "four_way_parity_positive": "PASS_TRUE_HIGHER_ORDER_AFFINE_INVARIANT",
        "unconstrained_transition_negative": "PASS_ZERO_AFFINE_INVARIANTS",
        "positive_final_kernel": positive["complete_affine_GF2_kernel_vectors"],
        "negative_final_kernel": neg["complete_affine_GF2_kernel_vectors"],
        "positive_witness_count": positive["number_of_independent_source_model_witnesses"],
        "negative_witness_count": neg["number_of_independent_source_model_witnesses"],
    }


def examine_original(root: Path, max_ms: int):
    spec = next((p, digest) for p, digest in ORIGINS if p == TARGET)
    p, expected_git_blob = spec
    started = time.perf_counter_ns()
    result = {
        "target": p, "source_git_blob": expected_git_blob,
        "scientific_status": "NOT_TESTED",
        "global_Q3": "OPEN",
    }
    raw = (root / p).read_bytes()
    if blob(raw) != expected_git_blob:
        raise RuntimeError("FROZEN_AUTHENTIC_SOURCE_BLOB_MISMATCH")
    result["actual_source_sha256"] = sha(raw)
    sex = sexprs(raw)
    typed = compile_typed_original(sex)
    native = compile_independent_native(sex, typed)
    parity = {k: dual(z3.Xor(typed[k], native[k]), "unsat", 10)
              for k in ("pre", "trans", "post")}
    result["native_independent_original_source_semantic_parity"] = parity
    if not all(x["dual_pass"] for x in parity.values()):
        raise RuntimeError("ORIGINAL_SOURCE_SEMANTIC_MISMATCH_ABSTAIN")
    original = {**typed, **native}
    goal_support = {str(x) for x in z3.z3util.get_vars(native["post"])}
    eligible = [i for i, (_, sort) in enumerate(typed["states"])
                if sort == "Bool" and str(typed["now"][i]) not in goal_support]
    result["eligible_source_bool_original_state_indices"] = eligible
    if len(eligible) != 20:
        raise RuntimeError("HISTORICALLY_FROZEN_DRAGON_BOOL_WIDTH_CHANGED")
    fixedpoint = converge(original["pre"], original["trans"],
                          original["now"], original["next"],
                          eligible, max_ms)
    result["fixedpoint"] = fixedpoint
    if fixedpoint["status"] != "Z3_EXACT_LEAST_AFFINE_FIXEDPOINT_OBTAINED":
        result["scientific_status"] = "ABSTAIN_CEGIS_DID_NOT_CONVERGE"
        return result

    vectors = fixedpoint["complete_affine_GF2_kernel_vectors"]
    inv = kernel_expr(vectors, original["now"], eligible)
    nxt = kernel_expr(vectors, original["next"], eligible)
    # FIRST independent Z3+cvc5 proof for FULL final conjunction.
    proofs = {
        "actual_original_Pre_implies_full_affine_invariant":
            dual(z3.And(original["pre"], z3.Not(inv)),
                 "unsat", DUAL_TIMEOUT_S),
        "actual_original_invariant_and_Trans_implies_next_invariant":
            dual(z3.And(inv, original["trans"], z3.Not(nxt)),
                 "unsat", DUAL_TIMEOUT_S),
    }
    result["final_original_global_affine_2VC_Z3_and_cvc5"] = proofs
    if not all(x["dual_pass"] for x in proofs.values()):
        result["scientific_status"] = "ABSTAIN_INDEPENDENT_ORIGINAL_2VC_UNPROVED"
        return result

    rows = fixedpoint["source_witnesses"]
    exact_pair_basis, pair_report = sample_pairwise_basis(rows, len(eligible))
    result["affine_hull_pairwise_rank"] = len(exact_pair_basis)
    result["affine_hull_sample_pairwise_accounting"] = pair_report
    result["affine_full_vs_pairwise_abstract_rank_gap"] = (
        len(vectors) - len(exact_pair_basis))
    certified_low = {}
    low_results = []
    for width in (1, 2):
        for cols in itertools.combinations(range(len(eligible)), width):
            offset = sum(rows[0][i] for i in cols) % 2
            if any(sum(row[i] for i in cols) % 2 != offset for row in rows):
                continue
            value = sum(1 << i for i in cols) | (offset << len(eligible))
            expression = candidate_original_native(
                original, eligible, value & ((1 << len(eligible)) - 1), offset)
            proof = independent_original_2vc(original, expression)
            works = bool(proof["full_two_vc_dual_original"])
            independent = add_pivot(certified_low, value) if works else False
            low_results.append({
                "original_source_bool_indices": [eligible[i] for i in cols],
                "offset": offset, "original_independently_inductive": works,
                "new_GF2_dimension": independent, "actual_original_dual_2VC": proof,
            })
    result["all_low_arity_candidates_source_2VC"] = low_results
    result["program_individually_inductive_low_arity_GF2_rank"] = len(certified_low)
    result["exact_full_inductive_GF2_nullity"] = len(vectors)
    result["every_affine_2VC_true_invariant_covered"] = True
    result["all_actual_original_affine_invariants_individually_low_arity_generated"] = (
        len(certified_low) == len(vectors))
    result["strictly_independent_higher_arity_affine_headroom"] = (
        len(certified_low) < len(vectors))
    result["scientific_status"] = (
        "CERTIFIED_FULL_ORIGINAL_AFFINE_CLOSURE_LOW_ARITY_COMPLETE"
        if result["all_actual_original_affine_invariants_individually_low_arity_generated"]
        else "CERTIFIED_FULL_ORIGINAL_AFFINE_CLOSURE_HIGHER_ORDER_BASIS_EXISTS"
    )
    result["science_limits"] = {
        "no_new_neural_learned_math_operator": True,
        "no_learned_first_original_3VC": True,
        "not_full_program_nonaffine_invariant_closure": True,
        "only_pinned_DRAGON_2_goal_excluded_Bool_state_scope": True,
        "learned_first_XOR4_0of2_preserved": True,
        "Q3_GateR_GateV_global": "OPEN",
    }
    result["total_wall_ms"] = elapsed(started)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--first", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--max-wall-ms", type=int, default=600000)
    a = ap.parse_args()
    first_bytes = a.first.read_bytes()
    if sha(first_bytes) != FROZEN_FIRST_LEARNED_SHA:
        raise RuntimeError("IMMUTABLE_FIRST_BLIND_XOR4_SOURCE_RECEIPT_CHANGED")
    first = json.loads(first_bytes)
    if first["learned_independent_real_original_2VC_count"] != 0 or \
       first["strong_classical_independent_real_original_2VC_count"] != 0:
        raise RuntimeError("HISTORICAL_FIRST_0_OF_2_NOT_PRESERVED")
    result = {
        "schema": "neumann.q3.least_affine_real_original_GF2_source.v1",
        "run_scope": "POSTHOC_CLASSICAL_NOT_NEURAL_Q3_SUCCESS",
        "first_frozen_neural_source_SHA256": FROZEN_FIRST_LEARNED_SHA,
        "historic_first_real_learned_XOR4": "0/2_PRESERVED",
        "upstream_source_revision": UPSTREAM,
        "controls": synthetic_controls(),
        "original": examine_original(a.root, a.max_wall_ms),
        "GPU": 0, "paid_API": 0, "new_training_updates": 0,
        "global_Q3": "OPEN", "full_Q3_GateR_and_GateV": "OPEN",
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("EXACT_AFFINE_GF2_FINAL_STATUS",
          result["original"]["scientific_status"], flush=True)
    print("AFFINE_GF2_COMPLETE_RANK",
          result["original"].get("exact_full_inductive_GF2_nullity", "UNKNOWN"),
          "SCOPE", TARGET, flush=True)
    print("GLOBAL_Q3", result["global_Q3"], flush=True)


if __name__ == "__main__":
    main()
