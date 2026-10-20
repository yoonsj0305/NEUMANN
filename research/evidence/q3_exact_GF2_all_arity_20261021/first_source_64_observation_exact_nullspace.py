"""NEUMANN Q3 source-specific GF(2) theorem for ALL XOR arities.

Do not train another model. Exactly compare the full observed-state affine GF2
nullspace to the singleton/pairwise span on the same 64 actual original source
states. All calculations exact integer XOR, all source identities pinned.
Preserve original first learned-XOR4 0/2 CI JSON immutable; if a residual
exists, check native original Z3+cvc5 initial and consecution instead of
asserting it is an inductive invariant.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import time
from pathlib import Path

import z3

from research.evidence.q3_gateR_learned_xor4_20261021.first_two_frozen_source_four_way_parity import (
    ORIGINS, UPSTREAM, blob, sha, sexprs, compile_typed_original,
    compile_independent_native, dual, samples, sample_pairwise_basis,
    gf2_in_span, elapsed,
)

FIRST_ORIGINAL_SHA256 = "5e9c7f5d1e4039d5a7e3b7edd90857684d8d7ac14b3ab10589b76c2102c2e47b"


def add_pivot(rows, vector):
    """Represent a GF2 vector by rows pivoted on its highest set bit."""
    original = vector
    while vector:
        p = vector.bit_length() - 1
        if p not in rows:
            rows[p] = vector
            return True
        vector ^= rows[p]
    return False


def reduce_basis(rows, vector):
    while vector:
        p = vector.bit_length() - 1
        if p not in rows:
            return vector
        vector ^= rows[p]
    return 0


def nullspace_matrix(samples_of_true_states, n):
    # Parity relation dot(mask, state) = affine-offset is equivalent to
    # dot((state, 1), (mask, offset)) = 0 over GF(2).
    constraint_pivots = {}
    for source_state in samples_of_true_states:
        assert len(source_state) == n
        row = (1 << n) | sum(int(bit) << j for j, bit in enumerate(source_state))
        add_pivot(constraint_pivots, row)
    free_columns = [p for p in range(n + 1) if p not in constraint_pivots]
    vectors = []
    for free in free_columns:
        candidate = 1 << free
        # The highest-pivot row only depends on lower-order columns,
        # hence solve pivot variables in increasing pivot order.
        for pivot in sorted(constraint_pivots):
            if (constraint_pivots[pivot] & candidate).bit_count() % 2:
                candidate ^= 1 << pivot
        for observed in samples_of_true_states:
            value = (1 << n) | sum(int(bit) << j for j, bit in enumerate(observed))
            if (value & candidate).bit_count() % 2:
                raise RuntimeError("INTERNAL_GAUSS_NULLSPACE_CONSTRUCTION_INCORRECT")
        vectors.append(candidate)
    expected_nullity = (n + 1) - len(constraint_pivots)
    if len(vectors) != expected_nullity:
        raise RuntimeError("GF2_NULLITY_DIMENSION_MISMATCH")
    indep = {}
    for v in vectors:
        if not add_pivot(indep, v):
            raise RuntimeError("NULLSPACE_BASIS_NOT_LINEALLY_INDEPENDENT")
    return constraint_pivots, vectors


def candidate_original_native(source, eligible, mask, intercept):
    xs = [source["now"][eligible[i]] for i in range(len(eligible)) if (mask >> i) & 1]
    if not xs:
        raise RuntimeError("TRIVIAL_AFFINE_RELATION_IN_PROOF")
    value = z3.BoolVal(False)
    for term in xs:
        value = z3.Xor(value, term)
    return value == z3.BoolVal(bool(intercept))


def independent_original_2vc(original, candidate):
    step = z3.substitute(candidate, *list(zip(original["now"], original["next"])))
    init = dual(z3.And(original["pre"], z3.Not(candidate)), "unsat", 10)
    consequence = (
        dual(z3.And(candidate, original["trans"], z3.Not(step)), "unsat", 10)
        if init["dual_pass"]
        else {"status": "NOT_CHECKED_INITIAL_NOT_PROVED"}
    )
    return {
        "initial_actual_original": init,
        "consecution_actual_original": consequence,
        "full_two_vc_dual_original": bool(
            init["dual_pass"] and consequence.get("dual_pass")
        ),
    }


def source_decision(root, original_spec, historical):
    start = time.perf_counter_ns()
    path, expected_blob = original_spec
    out = {
        "original_source": path,
        "expected_git_blob": expected_blob,
        "scientific_status": "UNASSESSED",
        "original_full_native_parity_3of3_dual": False,
        "full_GF2_equivalence_proven_on_original_observations": False,
    }
    try:
        raw = (root / path).read_bytes()
        if blob(raw) != expected_blob:
            raise RuntimeError("FROZEN_SOURCE_BYTE_BLOB_MISMATCH")
        out["actual_original_sha256"] = sha(raw)
        parsed = compile_typed_original(sexprs(raw))
        native = compile_independent_native(sexprs(raw), parsed)
        checks = {
            field: dual(z3.Xor(parsed[field], native[field]), "unsat", 10)
            for field in ("pre", "trans", "post")
        }
        out["typed_original_vs_independent_native_3VC"] = checks
        if not all(v["dual_pass"] for v in checks.values()):
            raise RuntimeError("ACTUAL_ORIGINAL_PRE_TRANS_POST_SEMANTICS_UNCERTIFIED")
        out["original_full_native_parity_3of3_dual"] = True
        original = {**parsed, **native}
        post_support = {str(x) for x in z3.z3util.get_vars(native["post"])}
        eligible = [
            i for i, (_, sort) in enumerate(parsed["states"])
            if sort == "Bool" and str(parsed["now"][i]) not in post_support
        ]
        out["eligible_original_boolean_indices"] = eligible
        if eligible != historical["eligible_source_boolean_state_indices"]:
            raise RuntimeError("HISTORICAL_ORIGINAL_ELIGIBLE_SOURCE_VARIABLES_CHANGED")
        rows, source_sample_receipts = samples(original, eligible)
        out["source_original_sample_covered"] = source_sample_receipts
        out["observed_source_state_count"] = len(rows)
        if len(rows) != 64 or historical["original_source_only_64_or_fewer_observed_models"] != 64:
            raise RuntimeError("NOT_SAME_ACTUAL_SOURCE_64_OBSERVATIONS")
        if not all(not c["source_sample_consistent_all"]
                   for c in historical["original_first_frozen_learner_48_or_fewer"]):
            raise RuntimeError("HISTORICAL_FIRST48_UNEXPECTED_SOURCE_CONSISTENCY")
        out["historical_first_48_neural_all_sample_inconsistent"] = True
        n = len(eligible)
        row_basis, kernel_basis = nullspace_matrix(rows, n)
        pair_basis, pair_receipt = sample_pairwise_basis(rows, n)
        out["GF2_observation_row_rank"] = len(row_basis)
        out["GF2_complete_affine_nullity"] = len(kernel_basis)
        out["observed_source_singleton_pairwise_span"] = pair_receipt
        if pair_receipt["GF2_pairwise_span_rank"] != historical["source_sample_pairwise_upper_bound_on_inductive_span"]["GF2_pairwise_span_rank"]:
            raise RuntimeError("HISTORICAL_PAIRWISE_GF2_RANK_REGRESSION")
        out["all_observed_pairwise_relations_actually_in_nullspace"] = all(
            ((vector & ((1 << n) | sum(int(bit) << j for j, bit in enumerate(observed)))).bit_count() % 2) == 0
            for vector in pair_basis.values() for observed in rows
        )
        if not out["all_observed_pairwise_relations_actually_in_nullspace"]:
            raise RuntimeError("GF2_PAIRWISE_SOURCE_NOT_IN_COMPLETE_NULLSPACE")

        # Pair nullspace basis subset must always hold. If dimensions match,
        # their equality proves FULL observed affine XOR grammar closure.
        out["full_GF2_equivalence_proven_on_original_observations"] = (
            len(pair_basis) == len(kernel_basis)
            and all(gf2_in_span(pair_basis, vector) for vector in kernel_basis)
        )
        residuals = [v for v in kernel_basis if not gf2_in_span(pair_basis, v)]
        out["remaining_independent_affine_GF2_nullspace_basis_count"] = len(residuals)
        out["source_eligible_variable_count"] = n
        out["all_arity_residual_Gf2_candidates_examined"] = 0
        out["genuinely_source_independent_high_arity_xor_proof"] = None

        if out["full_GF2_equivalence_proven_on_original_observations"]:
            out["scientific_status"] = "CLOSED_NO_HIGHER_ORDER_INDEPENDENT_GF2_PARITY_ON_THESE_64_SOURCE_OBSERVATIONS"
            out["no_novel_GF2_parity_of_any_arity_possible_on_these_observations"] = True
        else:
            # Exact quotient witness without relying on neural scores.
            # Enumerate the quotient of kernel by pairwise, capped to
            # avoid spending money/time for no clear scientific yield.
            total_dim = len(kernel_basis)
            if total_dim > 16:
                out["scientific_status"] = "INCOMPLETE_KERNEL_QUOTIENT_MORE_THAN_65536"
            else:
                choices = []
                for selector in range(1, 1 << total_dim):
                    v = 0
                    for bit in range(total_dim):
                        if selector & (1 << bit):
                            v ^= kernel_basis[bit]
                    if gf2_in_span(pair_basis, v):
                        continue
                    mask = v & ((1 << n) - 1)
                    arity = mask.bit_count()
                    if arity >= 3:
                        choices.append((arity, mask, (v >> n) & 1))
                out["all_arity_residual_Gf2_candidates_examined"] = len(choices)
                if not choices:
                    out["scientific_status"] = "GF2_RESIDUAL_WITHOUT_NONTRIVIAL_CLAUSE"
                else:
                    arity, mask, offset = min(choices)
                    expr = candidate_original_native(original, eligible, mask, offset)
                    proof = independent_original_2vc(original, expr)
                    out["genuinely_source_independent_high_arity_xor_proof"] = {
                        "minimal_degree": arity, "source_eligible_mask": mask,
                        "xor_equals": offset, "actual_original_independent_2VC": proof,
                        "clause_smt": expr.sexpr(),
                    }
                    out["scientific_status"] = (
                        "CLASSICAL_SOURCE_DISCOVERED_NEW_HIGHER_ORDER_INDUCTIVE_GF2_RELATION"
                        if proof["full_two_vc_dual_original"]
                        else "CLASSICAL_GF2_SAMPLE_RESIDUAL_NOT_ORIGINAL_INDUCTIVE"
                    )
    except Exception as exc:
        out["scientific_status"] = "ABSTAIN_SOURCE_OR_GF2_AUDIT_ERROR"
        out["error"] = type(exc).__name__ + ": " + str(exc)[:360]
    out["source_wall_ms"] = elapsed(start)
    print(
        "EXACT_ALL_ARITY_GF2",
        out["original_source"],
        out["scientific_status"],
        "NULLITY", out.get("GF2_complete_affine_nullity"),
        "PAIRWISE", out.get("observed_source_singleton_pairwise_span", {}).get("GF2_pairwise_span_rank"),
        "ERROR", out.get("error"), flush=True,
    )
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--first", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    start = time.perf_counter_ns()
    original_first_bytes = args.first.read_bytes()
    if sha(original_first_bytes) != FIRST_ORIGINAL_SHA256:
        raise RuntimeError("FIRST_SOURCE_BLIND_JSON_ID_CHANGED")
    original_first = json.loads(original_first_bytes)
    assert original_first["first_two_original_file_Git_blobs_frozen_before_source_body_read"]
    assert original_first["learned_independent_real_original_2VC_count"] == 0
    assert original_first["strong_classical_independent_real_original_2VC_count"] == 0
    assert len(original_first["cases"]) == 2
    for source, old_row in zip(ORIGINS, original_first["cases"]):
        if source[0] != old_row["original"]:
            raise RuntimeError("HISTORICAL_ORIGINAL_SOURCE_ORDER_CHANGED")
    result = [
        source_decision(args.root, source, old)
        for source, old in zip(ORIGINS, original_first["cases"])
    ]
    doc = {
        "schema": "neumann.q3.exact_all_arity_affine_GF2_original_states.v1",
        "original_first_source_run": 39514997383,
        "immutable_original_first_JSON_sha256": FIRST_ORIGINAL_SHA256,
        "first_source_model_XOR4_2VC": "0/2_PRESERVED",
        "first_source_strong_classical_XOR4_2VC": "0/2_PRESERVED",
        "source_previously_opened_POSTHOC": True,
        "source_original_Git_SHA_revision": UPSTREAM,
        "all_original_byte_git_blobs_authenticated": all(
            "actual_original_sha256" in r for r in result
        ),
        "first_neural_synthetic_accuracy": "590/600",
        "first_matched_classical_synthetic_accuracy": "600/600",
        "source_specific_GF2_complete_closure_count": sum(
            r["full_GF2_equivalence_proven_on_original_observations"] for r in result
        ),
        "original_source_semantics_dual_3VC_count": sum(
            r["original_full_native_parity_3of3_dual"] for r in result
        ),
        "no_new_learned_model_training": True,
        "full_first_source_safety_3VC_by_learned_model": "NOT_DEMONSTRATED",
        "learned_new_math_primitive": "NOT_DEMONSTRATED",
        "gate_R_learned_novel_representation": "OPEN",
        "gate_V_first_new_author_origin": "OPEN",
        "global_Q3": "OPEN", "global_Q1_Q7": "OPEN",
        "GPU_calls": 0, "paid_API_calls": 0,
        "study_wall_ms": elapsed(start), "original_sources": result,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    print("FULL_GF2_ALL_ARITY_SOURCE_SPECIFIC_CLOSED",
          doc["source_specific_GF2_complete_closure_count"], "/2")
    print("GLOBAL_Q3", doc["global_Q3"])


if __name__ == "__main__":
    main()
