"""First unopened four real-original programs, already Git-blob frozen.

Classical exact source proof only. No learned transfer claim.
Zero model inference/training; records every FAIL/UNKNOWN with original identity.
"""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path

import z3

from research.evidence.q3_exact_GF2_all_arity_20261021.first_source_64_observation_exact_nullspace import (
    blob, sha, sexprs, compile_typed_original, compile_independent_native,
    dual, candidate_original_native, add_pivot, nullspace_matrix, elapsed
)
from research.evidence.q3_exact_GF2_all_arity_20261021.dragon2_exact_affine_inductive_fixpoint import (
    converge, kernel_expr, synthetic_controls, QUERY_TIMEOUT_MS, DUAL_TIMEOUT_S
)

UPSTREAM = "13c8deb68a873635879c9a69bc78caebd340f646"
MAX_WIDTH = 32

def transfer_source(root, entry, max_ms):
    start = time.perf_counter_ns()
    rec = {
        "source": entry["path"],
        "pre_registered_git_blob": entry["git_blob"],
        "status": "ABSTAIN_UNASSESSED",
        "learned_training_updates": 0,
        "neural_forward_calls": 0,
        "global_Q3": "OPEN",
    }
    try:
        data = (root / entry["path"]).read_bytes()
        if len(data) != entry["bytes"] or blob(data) != entry["git_blob"]:
            raise RuntimeError("PRESOURCE_METADATA_GIT_BLOB_OR_BYTES_CHANGED")
        rec["source_bytes_sha256"] = sha(data)
        parsed = compile_typed_original(sexprs(data))
        native = compile_independent_native(sexprs(data), parsed)
        rec["independent_native_typed_original_three_predicate_parity"] = {
            k: dual(z3.Xor(parsed[k], native[k]), "unsat", 10)
            for k in ("pre", "trans", "post")
        }
        if not all(v["dual_pass"] for v in rec["independent_native_typed_original_three_predicate_parity"].values()):
            rec["status"] = "ABSTAIN_SOURCE_SEMANTIC_PARITY_FAILED"
            return rec
        original = {**parsed, **native}
        target_symbols = {str(v) for v in z3.z3util.get_vars(native["post"])}
        eligible = [
            i for i, (_, typ) in enumerate(parsed["states"])
            if typ == "Bool" and str(parsed["now"][i]) not in target_symbols
        ]
        rec["eligible_bool_original_state_indices"] = eligible
        if not 1 <= len(eligible) <= MAX_WIDTH:
            rec["status"] = "ABSTAIN_BOOL_WIDTH_OUTSIDE_1_32"
            return rec
        remaining_ms = max_ms - elapsed(start)
        if remaining_ms < 1000:
            rec["status"] = "ABSTAIN_TIMEOUT_BEFORE_FIXEDPOINT"
            return rec
        result = converge(original["pre"], original["trans"],
                          original["now"], original["next"],
                          eligible, remaining_ms)
        rec["least_affine_inductive_hull"] = result
        if result["status"] != "Z3_EXACT_LEAST_AFFINE_FIXEDPOINT_OBTAINED":
            rec["status"] = "ABSTAIN_EXACT_ORIGINAL_FIXEDPOINT_UNAVAILABLE"
            return rec
        final_vectors = result["complete_affine_GF2_kernel_vectors"]
        n = len(eligible)
        inv = kernel_expr(final_vectors, original["now"], eligible)
        inv_next = kernel_expr(final_vectors, original["next"], eligible)
        rec["final_original_conjunction_independent_dual_Z3_cvc5"] = {
            "init": dual(z3.And(original["pre"], z3.Not(inv)), "unsat", DUAL_TIMEOUT_S),
            "consecution": dual(z3.And(inv, original["trans"], z3.Not(inv_next)),
                                "unsat", DUAL_TIMEOUT_S),
        }
        if not all(q["dual_pass"] for q in rec["final_original_conjunction_independent_dual_Z3_cvc5"].values()):
            rec["status"] = "ABSTAIN_FULL_ORIGINAL_DUAL_2VC_FAILED"
            return rec
        # All genuine affine invariants in this projected scope are implied
        # by these genuine source-inductive full-conjunction basis clauses.
        # For stronger low-arity conclusion require INDIVIDUAL proof of each
        # independent singleton or pair clause. Skip dependent proposals.
        witness_rows = result["source_witnesses"]
        verified = {}
        failures = []
        successes = []
        for width in (1, 2):
            from itertools import combinations
            for columns in combinations(range(n), width):
                off = sum(witness_rows[0][k] for k in columns) % 2
                if any(sum(row[k] for k in columns) % 2 != off for row in witness_rows):
                    continue
                vector = sum(1 << k for k in columns) | (off << n)
                if not nullspace_matrix(witness_rows, n)[1]:
                    break
                if in_GF2(verified, vector):
                    continue
                if elapsed(start) > max_ms:
                    rec["status"] = "ABSTAIN_BUDGET_DURING_LOW_ARITY_PROOFS"
                    rec["number_verified_low_arity"] = len(verified)
                    return rec
                candidate = candidate_original_native(original, eligible,
                           vector & ((1 << n) - 1), off)
                cand_next = z3.substitute(candidate, *list(zip(original["now"], original["next"])))
                pr = {
                    "initial": dual(z3.And(original["pre"], z3.Not(candidate)), "unsat", DUAL_TIMEOUT_S),
                    "step": dual(z3.And(candidate, original["trans"], z3.Not(cand_next)),
                                 "unsat", DUAL_TIMEOUT_S),
                }
                record = {"columns": [eligible[k] for k in columns],
                          "arity": width, "affine_vector": vector,
                          "independently_source_inductive": all(q["dual_pass"] for q in pr.values()),
                          "original_dual_2VC": pr}
                if record["independently_source_inductive"]:
                    add_pivot(verified, vector)
                    successes.append(record)
                else:
                    failures.append(record)
                if len(verified) == len(final_vectors):
                    break
            if len(verified) == len(final_vectors):
                break
        rec["proved_independent_lowarity_certificates"] = successes
        rec["failed_or_unknown_individually_checked_lowarity_candidates"] = failures
        rec["source_proven_lowarity_rank"] = len(verified)
        rec["full_affine_inductive_nullity"] = len(final_vectors)
        rec["source_true_affine_space_complete"] = True
        rec["all_true_affine_operators_reducible_to_individually_inductive_lowarity"] = (
            len(verified) == len(final_vectors)
        )
        rec["status"] = (
            "PASS_FULL_ORIGINAL_AFFINE_AND_LOWARITY_GENERATION"
            if rec["all_true_affine_operators_reducible_to_individually_inductive_lowarity"]
            else "PASS_FULL_ORIGINAL_AFFINE_FIXEDPOINT_HIGHER_ARITY_POSSIBLE"
        )
    except Exception as ex:
        rec["status"] = "ABSTAIN_EXCEPTION"
        rec["error"] = type(ex).__name__ + ":" + str(ex)[:380]
    finally:
        rec["wall_ms"] = elapsed(start)
        print("UNOPENED_ORIGINAL", rec["source"], rec["status"],
              "AFFINE_NULLITY", rec.get("full_affine_inductive_nullity"),
              "LOW_RANK", rec.get("source_proven_lowarity_rank"),
              "ERROR", rec.get("error"), flush=True)
    return rec


def in_GF2(basis, vector):
    while vector:
        high = vector.bit_length() - 1
        if high not in basis:
            return False
        vector ^= basis[high]
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--max-wall-ms", type=int, default=90000)
    opts = p.parse_args()
    frozen = json.loads(opts.freeze.read_text())
    if frozen["upstream_commit"] != UPSTREAM or len(frozen["source_targets"]) != 4:
        raise RuntimeError("FROZEN_REPOSITORY_OR_COHORT_CHANGED")
    controls = synthetic_controls()
    results = [
        transfer_source(opts.root, target, opts.max_wall_ms)
        for target in frozen["source_targets"]
    ]
    output = {
        "schema": "neumann.q3.frozen_first_classical_affine_four_originals.v1",
        "upstream_revision": UPSTREAM,
        "first_freeze_presource_commit": "8e6efc5b5a6f637ac6b92fbb459616e30ce97072",
        "all_source_names_precommitted_before_open": True,
        "source_cohort_same_author_family": True,
        "previous_fi_re_and_dragon_2_results_not_first": True,
        "controls": controls,
        "source_results": results,
        "num_authenticated_sources": sum(bool(r.get("source_bytes_sha256")) for r in results),
        "num_source_semantic_parity_dual_pass": sum(all(p["dual_pass"] for p in r.get(
            "independent_native_typed_original_three_predicate_parity", {}).values())
            and len(r.get("independent_native_typed_original_three_predicate_parity", {})) == 3
            for r in results),
        "num_exact_full_affine_original_dual_pass": sum(
            r.get("source_true_affine_space_complete", False) for r in results),
        "num_full_affine_lowarity_complete_original_dual_pass": sum(
            r.get("all_true_affine_operators_reducible_to_individually_inductive_lowarity", False)
            for r in results),
        "all_four_source_rows_preserved": len(results) == 4,
        "model_train_updates": 0, "model_inferences": 0, "paid_API_calls": 0, "GPU_calls": 0,
        "global_Q3": "OPEN", "global_Q4": "OPEN", "frontier_level": "NOT_DEMONSTRATED"
    }
    opts.out.parent.mkdir(parents=True, exist_ok=True)
    opts.out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print("FOUR_FIRST_SOURCE_EXACT_CERTIFIED", output["num_exact_full_affine_original_dual_pass"], "/4")
    print("FOUR_FIRST_SOURCE_STRONG_LOWARITY", output["num_full_affine_lowarity_complete_original_dual_pass"], "/4")
    print("GLOBAL_Q3", output["global_Q3"])
if __name__ == "__main__":
    main()
