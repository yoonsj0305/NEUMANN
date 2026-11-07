"""Post-audit source-frozen Q3 external CodeARC all remaining original IDs.

No post-CodeARC mutation of generic TypeGuidedInventor:
Git blob 01862093cf68c0a3425002a01fa8f83967bbcd23.
The unchanged evaluator source has Git blob
ca2c6c19119fa3fe724eb2471f95ad1439e0bec8.

Cohort: CodeARC original ID >20 and old hash bucket 2..16 inclusive.
All old development samples were bucket 0, first independent external
development cohort bucket 1. Remaining >=2 buckets contain only NEW source
task IDs to us, selected en bloc (NO score-informed cherry-picking).

The original evaluator uses bucket 1; this wrapper changes ONLY the target
ID selection by replacing fresh_target, and adds a STRICT post-hoc novelty
audit. It does not change expression interpreter, hypothesis generation,
fitted coefficients, type predicates, evaluation oracle, data version or
heldout split.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from research.q3 import codearc_typed_delta_novel_original_first as original
from research.q3.typed_semantic_delta_inventor import digest

SCHEMA="neumann.q3.full-remaining-codearc-nontrivial-novelty-audit.v1"
INVENTOR_BLOB="01862093cf68c0a3425002a01fa8f83967bbcd23"
EVALUATOR_BLOB="ca2c6c19119fa3fe724eb2471f95ad1439e0bec8"


def has_substantive_new_calculation(program):
    """Exclude constants and elementary primitive operations.

    A type name 'DerivedPolynomial' alone NEVER proves an invented operator.
    The post-first bucket1 false positive #446 was only f(x)=6 and is NOT
    a substantive invention, despite an older broad categorical tally.
    """
    if not isinstance(program,dict):return False
    kind=program.get("kind")
    if kind=="DerivedSequenceFilter":
        return bool(program.get("removed")) and (
            program.get("predicate_ast",[None])[0]=="lambda")
    if kind=="DerivedPolynomial":
        terms=[(expo,coeff) for expo,coeff in zip(
            program.get("monomials",[]),program.get("coefficients",[]))
            if coeff and coeff[0]!=0]
        if not terms:return False
        # Constant, identity and single scalar degree-one multiplication
        # are elementary, not new computational structure.
        degree=max(sum(e) for e,c in terms)
        active_terms=sum(sum(e)>0 for e,c in terms)
        return degree>=2 or active_terms>=2
    return False


def run(dataset:Path,out:Path,shard=0,shards=8):
    old=original.fresh_target
    try:
        original.fresh_target=lambda ident: (
            ident>20 and 2<=original.hash_bucket(ident)<=16)
        report=original.evaluate(dataset,out,shard,shards)
    finally:
        original.fresh_target=old
    oldsummary=report["summary"]
    assert all(2<=original.hash_bucket(q["original_id"])<=16
               for q in report["rows"])
    assert all(original.hash_bucket(q["original_id"]) not in (0,1)
               for q in report["rows"])
    detailed=[]
    for row in report["rows"]:
        program=row.get("generated_operator_AST")
        is_substantive=(
            row.get("all_3_test_exact",False)
            and has_substantive_new_calculation(program)
            and not row.get("old_core_all_3_exact",False))
        # This is an audit against a RESTRICTED baseline, not evidence of
        # new fundamental computability, trained model or global Q3.
        row["substantive_operator_grading"]=(
            "NONTRIVIAL_EXACT_SOURCE_DISTINCT" if is_substantive
            else "NO_SUBSTANTIVE_NEW_OPERATOR_EVIDENCE")
        row["constant_polynomial_rejected_as_novel"]=(
            program is not None and program.get("kind")=="DerivedPolynomial"
            and not has_substantive_new_calculation(program))
        detailed.append(row)
    summary={
        **oldsummary,
        "cohort_definition":"original old hash %17 in 2..16; all IDs >20",
        "first_first_cohort_buckets_excluded":[0,1],
        "substantive_new_nonconstant_operator_original_exact":sum(
            q["substantive_operator_grading"]=="NONTRIVIAL_EXACT_SOURCE_DISTINCT"
            for q in detailed),
        "constant_polynomial_FALSE_NOVELTY_count":sum(
            q.get("constant_polynomial_rejected_as_novel",False)
            for q in detailed),
        "exact_source_distinct_filter_programs":sum(
            q["substantive_operator_grading"]=="NONTRIVIAL_EXACT_SOURCE_DISTINCT"
            and q["generated_operator_AST"]["kind"]=="DerivedSequenceFilter"
            for q in detailed),
        "exact_source_distinct_nontrivial_polynomial_programs":sum(
            q["substantive_operator_grading"]=="NONTRIVIAL_EXACT_SOURCE_DISTINCT"
            and q["generated_operator_AST"]["kind"]=="DerivedPolynomial"
            for q in detailed)}
    report.update({
        "schema":SCHEMA,
        "summary":summary,
        "cohort_old_report_label_overridden":True,
        "proposer_source_blob_unchanged":INVENTOR_BLOB,
        "evaluator_source_blob_unchanged":EVALUATOR_BLOB,
        "no_novelty_for_constant_or_identity":True,
        "new_fundamental_primitive_invented":False,
        "scientific_status":"Q3_GLOBAL_OPEN",
        "rows":detailed})
    (out/"FIRST.json").write_text(json.dumps(
        report,indent=2,sort_keys=True)+"\n")
    (out/"NOVELTY_AUDIT.json").write_text(json.dumps({
        "schema":SCHEMA,"summary":summary,
        "nontrivial_originals":[{
            "id":q["original_id"],"AST":q["generated_operator_AST"],
            "heldout_test_exact":q["test_exact"],
            "source_proposals":q["proposals_with_memory"]}
            for q in detailed if q["substantive_operator_grading"]
                   =="NONTRIVIAL_EXACT_SOURCE_DISTINCT"],
        "false_novelty_const_count":summary[
            "constant_polynomial_FALSE_NOVELTY_count"]},
        sort_keys=True,indent=2)+"\n")
    print("Q3_FULL_REMAINING_ORIGINALS_STRICT_FIRST",
          json.dumps(summary,sort_keys=True),flush=True)
    for q in detailed:
        if q["substantive_operator_grading"]=="NONTRIVIAL_EXACT_SOURCE_DISTINCT":
            print("NONTRIVIAL_SOURCE_DISTINCT_EXACT",q["original_id"],
                  q["generated_operator_AST"],flush=True)
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dataset",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--shard",type=int,default=0)
    p.add_argument("--shards",type=int,default=8)
    args=p.parse_args()
    run(args.dataset,args.out,args.shard,args.shards)
