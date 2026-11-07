"""POSTFIRST development: relational representation inventor on exposed HumanEval.

All 164 official original task IDs were accessed by #715 first run, and
function #48's specification and reference were inspected after #716.
This is a mechanistic/symbolic proof case-study, never external blind Q3.
"""
from __future__ import annotations
import argparse,gzip,hashlib,json
from pathlib import Path
from research.q3.universal_fold_humaneval_postfirst_audit import extract_any
from research.q3.discover_index_relation_constructor import (
    discover,run_new_representation,coeffs,
)
from research.q3.universal_typed_state_fold_postfirst import (
    synthesis as old_synthesis,run as old_run,same
)

PINNED_SHA="b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef"

def run(path:Path,out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_POSTFIRST_RELATION_AUDIT")
    out.mkdir(parents=True)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=PINNED_SHA:
        raise RuntimeError("ORIGINAL_SOURCE_VERSION_CHANGED")
    with gzip.open(path,"rt",encoding="utf8") as f:
        corpus=[json.loads(line) for line in f if line.strip()]
    if len(corpus)!=164:raise ValueError("NOT_OFFICIAL_164")
    rows=[]
    for source in corpus:
        rec={"id":source.get("task_id"),
             "postfirst_NOT_NEW_BLIND":True,
             "external_author_code_not_read":True,
             "reference_prompt_not_read_by_inventor":True}
        try:
            all_cases=extract_any(source["test"])
            if any(type(y) is not bool for args,y in all_cases):
                raise ValueError("NOT_BOOLEAN_ORIGINAL_OUTPUT")
            source_only=all_cases[:-2]
            hidden=all_cases[-2:]
            invented=discover(source_only,budget=1200)
            old=old_synthesis(source_only,budget=5000)
            predictions=[invented["program"] is not None and
                         run_new_representation(invented["program"],args) is y
                         for args,y in hidden]
            old_pred=[old["program"] is not None and
                      same(old_run(old["program"],args),y)
                      for args,y in hidden]
            rec.update({
                "status":"EXACT" if all(predictions) else "WRONG_OR_ABSTAIN",
                "source_train_count":len(source_only),
                "source_original_heldout_count":len(hidden),
                "invented_representation_ast":invented["program"],
                "invented_relational_type":invented["status"],
                "affine_relation_coeffs":invented.get(
                    "coordinate_affine_coefficients"),
                "inventor_attempted_candidates":invented["attempts"],
                "inventor_ms":invented.get("wall_ms"),
                "old_unary_fold_program":old["program"],
                "old_program_attempts":old["attempts"],
                "original_heldout_exact":all(predictions),
                "original_heldout_correct":sum(predictions),
                "old_original_heldout_exact":all(old_pred),
                "old_original_heldout_correct":sum(old_pred),
                "incremental_relational_synthesis_exact":bool(
                    all(predictions) and not all(old_pred)),
            })
            if all(predictions):
                print("Q3_GENERATED_INDEX_RELATION_POSTFIRST_ORIGINAL_EXACT",
                      rec["id"],"AST",invented["program"],
                      "previous_unary_exact",all(old_pred),flush=True)
        except (ValueError,TypeError,KeyError,SyntaxError,
                IndexError,OverflowError,RecursionError,MemoryError) as e:
            rec.update({"status":"UNSUPPORTED",
                        "reason":(type(e).__name__+":"+str(e))[:190],
                        "source_original_heldout_count":0})
        rows.append(rec)
    scored=[r for r in rows if r.get("source_original_heldout_count")==2]
    evidence=next((r for r in rows if r["id"]=="HumanEval/48"),None)
    if evidence is None:raise RuntimeError("ORIGINAL_SOURCE_ID_MISSING")
    relation_certificate=None
    if evidence.get("original_heldout_exact") and \
       evidence.get("invented_representation_ast") is not None:
        program=evidence["invented_representation_ast"]
        # The affine coefficient theorem is EXACT for the entire AST
        # grammar {i,n,const,+,-} by structural induction.
        coeff=evidence["affine_relation_coeffs"]
        relation_certificate={
            "source_original_id":"HumanEval/48",
            "index_mapping_coefficients_i_n_constant":coeff,
            "index_mapping_mathematically_mirror_for_all_n":coeff==(-1,1,-1),
            "same_pairwise_comparator_eq":program["relation"]["compare"]=="eq",
            "reduction_all":program["relation"]["reduce"]=="all",
            "certifies_value_equality_to_reverse_for_any_sequence":bool(
                coeff==(-1,1,-1) and
                program["relation"]["compare"]=="eq" and
                program["relation"]["reduce"]=="all"),
            "reference_target_inspected_after_prior_FIRST":True,
        }
    summary={
        "source_total_original_HumanEval_tasks":164,
        "bool_sequence_to_bool_eligible":len(scored),
        "source_generated_relation_exact_on_2_original_heldout":sum(
            r["original_heldout_exact"] for r in scored),
        "previous_nonrelational_unary_fold_exact":sum(
            r["old_original_heldout_exact"] for r in scored),
        "relational_new_exact_over_unary_fold":sum(
            r["incremental_relational_synthesis_exact"] for r in scored),
        "new_symbolically_proven_relation_programs":sum(
            relation_certificate.get(
               "certifies_value_equality_to_reverse_for_any_sequence",False)
            for r in [evidence] if relation_certificate),
        "unsupported_boolean_or_io":164-len(scored),
        "post_first_exposed_originals":True,
        "external_blind_originals":0,
    }
    result={
        "schema":"neumann.q3.generic-pairwise-coordinate-repr-postfirst.v1",
        "original_first_source_actions_run":42361601013,
        "prior_generic_fold_development_run":42362322818,
        "official_original_sha256":PINNED_SHA,
        "source_reference_code_not_given_to_generator":True,
        "program_signature_and_proof_extracted_from_discovered_AST":True,
        "not_new_blind_oracle":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "summary":summary,"symbolic_certificate":relation_certificate,
        "rows":rows}
    (out/"POSTFIRST.json").write_text(
        json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print("Q3_INDEX_PAIR_RELATIONAL_POSTFIRST_AUDIT",
          json.dumps(summary,sort_keys=True),flush=True)
    print("Q3_GENERATED_RELATIONAL_SYMBOLIC_CERTIFICATE",
          json.dumps(relation_certificate,sort_keys=True),flush=True)
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--humaneval",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    run(x.humaneval,x.out)
