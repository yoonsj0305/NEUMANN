"""Q3Q2: independent ORIGINAL Post-only source theorem negative control.

No learned model is retrained/rerun, and no test solution is read. This asks
whether the SOURCE-GIVEN Post predicate itself is an inductive invariant.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,re,sys,time
from pathlib import Path
import z3

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3p-trained-typed-20261018"))
from first_trained_typed_proposer import load_specs,proof_vc

ORIGINAL_Q3Q_SHA256="cc921c0f08fd9c16ea4fa6e6a9a34eae4365f619b6e28fea5c88f2926b6c9521"
PROVEN="ALL_THREE_ORIGINAL_VCS_UNSAT_NONTRIVIAL"
def check(query):
    solver=z3.Solver();solver.set(timeout=3000);solver.add(query)
    try:return str(solver.check())
    except Exception:return "error"

def rough_family(name):
    stem=Path(name).name
    stem=re.sub(r"\.desugared\.sl$|\.sl$","",stem)
    for suffix in ("-new","_simp","_simpl","_vars"):
        stem=stem.replace(suffix,"")
    return stem

def run(root,priorfile):
    raw=priorfile.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_Q3Q_SHA256:
        raise ValueError("FROZEN_FIRST_Q3Q_NEURAL_ORIGINAL_RECEIPT_CHANGED")
    prior=json.loads(raw)
    if prior["status"]!="FIRST_CONSTRUCTIVE_NEURAL_TYPED_AST_ORIGINAL_PROOFS_RECORDED":
        raise ValueError("FIRST_TRAINED_Q3Q_NOT_COMPLETE")
    specs=load_specs(root)
    tests=[x for x in specs if x["split"]!="TRAIN"]
    originals={x["source_sha"]:x for x in prior["first_original_eval_sha_only"]}
    if len(tests)!=40 or {s["source_sha"] for s in tests}!=set(originals):
        raise ValueError("TEST_COHORT_ORIGINAL_BYTES_NOT_IDENTICAL_TO_FIRST")
    reports=[]
    for spec in tests:
        old=originals[spec["source_sha"]]
        if spec["path"]!=old["original_path"]:raise ValueError("ORIGINAL_SOURCE_PATH_MISMATCH")
        q3q=old.get("methods",{})
        learned=q3q.get("TRAINED_TOP12",{}).get("status")==PROVEN
        untrained=q3q.get("UNTRAINED_TOP12",{}).get("status")==PROVEN
        classical=q3q.get("CLASSICAL_ALL_GRAMMAR",{}).get("status")==PROVEN
        simple="ABSTAIN_UNSUPPORTED"
        checks=0;nontrivial=False
        if spec["parse_status"]=="OK" and spec["input_precondition_sat"]=="sat":
            neq=check(z3.Not(spec["post"]))
            nontrivial=neq=="sat"
            verdict,checks=proof_vc(spec["post"],spec,3000)
            simple=("SOURCE_POST_ALONE_ORIGINAL_INDUCTIVE_PROVEN"
                    if nontrivial and verdict=="ALL_THREE_ORIGINAL_VCS_UNSAT" else
                    "SOURCE_POST_ORIGINAL_NOT_CERTIFIED")
        reports.append({
          "source_sha":spec["source_sha"],"source_path":spec["path"],
          "split":spec["split"],"source_group":spec["group"],
          "rough_variant_family":rough_family(spec["path"]),
          "first_neural_constructed_conjunction_pass":learned,
          "first_untrained_conjunction_pass":untrained,
          "first_full_grammar_classical_pass":classical,
          "first_direct_spacer_original":old["classical_source_only_spacer_result"],
          "post_alone_status":simple,
          "post_alone_checked_vcs":checks,
          "post_alone_original_nontrivial":nontrivial,
          "learned_proof_beyond_source_post_alone":
              learned and simple!="SOURCE_POST_ALONE_ORIGINAL_INDUCTIVE_PROVEN"
        })
    summary={}
    for split in ("HELDOUT","DIAGNOSTIC"):
        xs=[x for x in reports if x["split"]==split]
        summary[split]={
            "exact_originals":len(xs),
            "source_post_alone_proves":sum(x["post_alone_status"]=="SOURCE_POST_ALONE_ORIGINAL_INDUCTIVE_PROVEN" for x in xs),
            "first_learned_source_constructed_proofs":sum(x["first_neural_constructed_conjunction_pass"] for x in xs),
            "first_learned_and_source_post_alone_both_prove":sum(
                x["first_neural_constructed_conjunction_pass"] and
                x["post_alone_status"]=="SOURCE_POST_ALONE_ORIGINAL_INDUCTIVE_PROVEN"
                for x in xs),
            "learned_proofs_not_provable_by_source_post_alone":sum(
                x["learned_proof_beyond_source_post_alone"] for x in xs),
            "learned_proof_variant_family_names":sorted({
                x["rough_variant_family"] for x in xs if x["first_neural_constructed_conjunction_pass"]}),
            "learned_proofs_not_solved_by_full_grammar_classical":sum(
                x["first_neural_constructed_conjunction_pass"] and not x["first_full_grammar_classical_pass"] for x in xs)
        }
    return {
      "study":"Q3Q2_FIXED_SAME_SOURCE_POST_ONLY_ORIGINAL_3VC_NEGATIVE_CONTROL",
      "status":"Q3Q2_ORIGINAL_POST_CONDITION_ONLY_CONTROL_COMPLETE",
      "original_first_Q3Q_json_sha256":ORIGINAL_Q3Q_SHA256,
      "source_programs":len(tests),
      "posthoc_explanation_only":True,
      "no_model_retraining_or_inference":True,
      "no_test_cover_or_published_answer_loaded":True,
      "no_q3f_challenge_originals_opened":True,
      "global_q1_q7":"OPEN",
      "by_split":summary,
      "per_exact_original":reports
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--first-q3q",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    report=run(a.root,a.first_q3q)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("Q3Q2_ORIGINAL_POST_ONLY_VS_NEURAL",report["by_split"])
    print("GLOBAL",report["global_q1_q7"])
