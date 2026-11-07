"""POST-FIRST role-generalization of a previously invented coordinate AST.

Original first GPCS data was accessed in #718. No blind claim is possible.
The same 29 author-created problems are uniformly evaluated, with identical
train/test random hash splits and equal per-target candidate budget.

Three arms:
1. prior learned coordinate AST + source-selected argument roles (budget 64)
2. cold generic coordinate grammar, NO source memory (budget 64)
3. cold same full grammar with budget 1200 (search-capacity diagnostic)

The human-coded component is generic role/operand binding, not an installed
mirror-image operator. Any exact original result is still post-first DEV
and cannot establish global Q3.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
from collections import Counter

from research.q3.gp_suite_connected_router_original_first import (
    load_training,load_prior_learned_representation
)
from research.q3.learn_argument_roles_for_prior_relation import (
    SCHEMA as ROLE_SCHEMA,acceptable,search,score,run_role_program
)

SCHEMA="neumann.q3.prior-affine-relation-auto-role-transfer-gpcs-postfirst.v1"


def run(dataset:Path,manifest_path:Path,source_memory:Path,out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_POSTFIRST")
    out.mkdir(parents=True)
    prior=load_prior_learned_representation(source_memory)
    manifest=json.loads(manifest_path.read_text())
    if len(manifest)!=29:raise ValueError("NOT_COMPLETE_ALL_29_ORIGINALS")
    receipts=[];t0=time.perf_counter_ns()
    for file in manifest:
        task=file["task"]
        record={"source_family":task,
                "original_author":"Thomas Helmuth / Lee Spector",
                "same_preexisting_input_hash_split":True,
                "not_new_independent_original":True,
                "source_problem_name_not_sent_to_inventor":True}
        try:
            if not file["downloaded"]:
                raise ValueError("FILE_NOT_DOWNLOADED")
            data=dataset/file["paths"]["edge"]
            random=dataset/file["paths"]["random"]
            train,hidden,meta=load_training(data,random)
            record.update(meta)
            if len(train)<6 or len(hidden)<16:
                raise ValueError("TOO_FEW_SOURCE_OR_TEST")
            if not acceptable(train):
                raise ValueError("NOT_TWO_INPUT_SEQUENCE_TO_BOOL")
            # Three source-only programs frozen independently before
            # any heldout output is used for scoring.
            warm=search(train,prior_program=prior["program"],budget=64)
            cold=search(train,prior_program=None,budget=64)
            full=search(train,prior_program=None,budget=1200)
            warm_score=score(warm["program"],hidden)
            cold_score=score(cold["program"],hidden)
            full_score=score(full["program"],hidden)
            record.update({
                "status":"SCORED",
                "source_training_examples":len(train),
                "heldout_independent_author_originals":len(hidden),
                "warm_with_source_memory":warm,
                "cold_same_64_program_budget":cold,
                "cold_larger_1200_program_budget":full,
                "warm_original_score":warm_score,
                "cold_64_original_score":cold_score,
                "cold_1200_original_score":full_score,
                "prior_memory_causally_new_exact":(
                    warm_score["exact"] and not cold_score["exact"]
                    and warm["status"]=="TRANSFERRED_NEW_INPUT_ROLE_BINDING"),
                "prior_memory_expression_reused":(
                    warm["status"]=="TRANSFERRED_NEW_INPUT_ROLE_BINDING"),
            })
            if warm_score["exact"] or cold_score["exact"] or full_score["exact"]:
                print("Q3_GP_ROLE_TRANSFER_POSTFIRST_EXACT",task,
                      "memory",warm_score["exact"],
                      "cold64",cold_score["exact"],
                      "cold1200",full_score["exact"],
                      "source_memory_used",record["prior_memory_expression_reused"],
                      "warm_ast",warm["program"],flush=True)
        except (ValueError,TypeError,KeyError,OSError,EOFError,
                IndexError,UnicodeError,RecursionError,OverflowError) as e:
            record["status"]="UNSUPPORTED"
            record["reason"]=f"{type(e).__name__}:{e}"[:180]
        receipts.append(record)
    eligible=[r for r in receipts if r["status"]=="SCORED"]
    summary={
       "original_program_families_total":len(manifest),
       "original_families_two_sequence_inputs_to_bool":len(eligible),
       "original_families_other_type_unhandled":29-len(eligible),
       "source_invented_coordinate_reused_on_new_input_roles":sum(
           r["prior_memory_expression_reused"] for r in eligible),
       "memory_exact_on_32_original_test_inputs":sum(
           r["warm_original_score"]["exact"] for r in eligible),
       "cold_same_budget64_full_exact":sum(
           r["cold_64_original_score"]["exact"] for r in eligible),
       "cold_larger_budget1200_full_exact":sum(
           r["cold_1200_original_score"]["exact"] for r in eligible),
       "CAUSAL_MEMORY_ADVANTAGE_64_BUDGET_EXACT":sum(
           r["prior_memory_causally_new_exact"] for r in eligible),
       "memory_original_test_items_correct":sum(
           r["warm_original_score"]["correct"] for r in eligible),
       "heldout_original_items_tested":sum(
           r["warm_original_score"]["tested"] for r in eligible),
       "program_candidate_checks_mem64":sum(
           r["warm_with_source_memory"]["attempts"] for r in eligible),
       "program_candidate_checks_cold64":sum(
           r["cold_same_64_program_budget"]["attempts"] for r in eligible),
       "program_candidate_checks_cold1200":sum(
           r["cold_larger_1200_program_budget"]["attempts"] for r in eligible),
       "all_external_source_target_data_previously_exposed":True,
       "elapsed_all_source_train_ms":round(
           (time.perf_counter_ns()-t0)/1e6,4),
    }
    result={
       "schema":SCHEMA,
       "original_29_first_run":42365072610,
       "previous_29_complete_postfirst":42365349653,
       "parent_source_memory_artifact_run":42363017165,
       "source_memory_ast_sha256":prior["sha256"],
       "generic_role_binding_human_authored":True,
       "source_coordinate_formula_NOT_MANUALLY_ADDED":True,
       "source_original_reference_program_unread":True,
       "not_independent_first":True,
       "Q3_GLOBAL":"OPEN","Q4_GLOBAL":"OPEN","Q6_GLOBAL":"OPEN",
       "summary":summary,"rows":receipts,
    }
    (out/"POSTFIRST.json").write_text(json.dumps(
        result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print("Q3_GP_ALL_29_PRIOR_RELATION_NEW_ARGUMENT_ROLE_TRANSFER",
          json.dumps(summary,sort_keys=True),flush=True)
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--data",required=True,type=Path)
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--source-memory",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    run(a.data,a.manifest,a.source_memory,a.out)
