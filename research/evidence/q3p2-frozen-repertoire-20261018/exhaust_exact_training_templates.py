"""Q3P-2 finite original-proof AST template repertoire exhaustion, NO retraining.

All candidate original formulas are from frozen Q3P training originals only.
The predeclared heldout source groups are inspected after Q3P first,
strictly for post-hoc representation coverage diagnosis. No solutions added.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,sys,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3p-trained-typed-20261018"))
from first_trained_typed_proposer import (
    load_specs,extract_template,transfer,proof_vc,SEED,TRAIN_GROUPS,
    TEST_VC_TIMEOUT,EXPECTED_LICENSE_BLOB
)
from first_trained_typed_proposer import blobhash

Q3P_FIRST_JSON_SHA="869f615ff04c134bd45f1d95c4291122d6fbf61837f6910ef5a8dcf5292fc74f"

def run(root,first_receipt_file):
    original=first_receipt_file.read_bytes()
    if hashlib.sha256(original).hexdigest()!=Q3P_FIRST_JSON_SHA:
        raise ValueError("FIRST_NEURAL_ORIGINAL_RESULT_RECEIPT_IDENTITY_CHANGED")
    prior=json.loads(original)
    if prior["status"]!="FIRST_FROZEN_LEARNED_TYPED_SOURCE_ONLY_PROOF_AUDIT_COMPLETE":
        raise ValueError("NEURAL_FIRST_RESULT_INCOMPLETE")
    if prior["strict_original_proven_distinct_training_AST_templates"]!=11:
        raise ValueError("FROZEN_11_ORIGINAL_TEMPLATES_NOT_MATCHING")
    if blobhash((root/"LICENSE.md").read_bytes())!=EXPECTED_LICENSE_BLOB:
        raise ValueError("SOURCE_RIGHTS_METADATA_CHANGED")
    sources=load_specs(root)
    train=[x for x in sources if x["split"]=="TRAIN" and
           x["parse_status"]=="OK" and x["input_precondition_sat"]=="sat"]
    test=[x for x in sources if x["split"]!="TRAIN"]
    indexed={(x["original_path"],x["original_sha"]) for x in prior["evaluation_original_records"]}
    if {(x["path"],x["source_sha"]) for x in test}!=indexed:
        raise ValueError("POSTHOC_TEST_ORIGINALS_DIFFER_FROM_FIRST_MODEL")
    oracle_specs=[]
    seen=set()
    extracted=[]
    t0=time.perf_counter_ns()
    for original_source in train:
        candidate,_=extract_template(original_source)
        if candidate and candidate["sha256"] not in seen:
            seen.add(candidate["sha256"])
            extracted.append(candidate)
            oracle_specs.append(candidate["original_training_source_sha"])
    if len(extracted)!=11 or oracle_specs!=prior["template_family_source_sha256"]:
        raise ValueError("FROZEN_CANDIDATE_LIST_CHANGED_NO_ORACLE_ALLOWED")
    results=[]
    statuses=collections.Counter()
    for testsource in test:
        old=next(x for x in prior["evaluation_original_records"]
                 if x["original_sha"]==testsource["source_sha"])
        case={
            "source_path":testsource["path"],"source_sha":testsource["source_sha"],
            "split":testsource["split"],"origin_group":testsource["group"],
            "actual_first_learned_top3":old.get(
                "independently_original_VC_successes_by_method",{}).get(
                  "TRAINED",{}).get("3",0),
            "first_model_classical_spacer":old["comparable_source_only_classical_specialist"],
            "new_operator_or_model_training":False,
        }
        if testsource["parse_status"]!="OK":
            case["status"]="ORIGINAL_SOURCE_NOT_SUPPORTED"
            case["available_templates"]=0
            case["fully_original_VC_proven_templates"]=0
            case["unknown_or_error_templates"]=0
        else:
            elig=[]
            for template in extracted:
                cand=transfer(template,testsource)
                if cand is not None:elig.append((template,cand))
            case["available_templates"]=len(elig)
            if len(elig)!=old.get("eligible_candidates",0):
                raise ValueError("FIRST_EVALUATION_CANDIDATE_ARITY_CHANGED")
            proofed=0;uncertain=0;bad=0;attempts=0
            for templ,proposed in elig:
                result,num=proof_vc(proposed,testsource,TEST_VC_TIMEOUT)
                attempts+=num
                statuses[result]+=1
                if result=="ALL_THREE_ORIGINAL_VCS_UNSAT":proofed+=1
                elif result in ("ABSTAIN_UNKNOWN","ABSTAIN_BACKEND_ERROR",
                               "ABSTAIN_UNBOUND_SOURCE_VARIABLE","ABSTAIN_NOT_BOOLEAN"):uncertain+=1
                else:bad+=1
            case.update({
                "status":("NO_ARITY_COMPATIBLE_TRAINING_INVARIANT" if not elig else
                          "REPRESENTATION_HAS_SOURCE_VALID_ORIGINAL_AST" if proofed else
                          "NO_SOURCE_VALID_AST_EXCEPT_UNCERTAIN_PROOF" if uncertain else
                          "ALL_CANDIDATES_ORIGINAL_VC_REFUTED"),
                "fully_original_VC_proven_templates":proofed,
                "unknown_or_error_templates":uncertain,
                "original_VC_refuted_templates":bad,
                "original_proof_VC_query_attempts":attempts,
                "candidate_formula_or_source_exported":False
            })
        if case["actual_first_learned_top3"] and not case["fully_original_VC_proven_templates"]:
            raise ValueError("FIRST_TRUE_LEARNED_PROOF_DISAGREES_WITH_COMPLETE_REPERTOIRE")
        results.append(case)
    buckets={}
    for label in ("HELDOUT","DIAGNOSTIC"):
        subset=[x for x in results if x["split"]==label]
        buckets[label]={
            "originals":len(subset),
            "originals_with_zero_arity_compatible_templates":sum(
                x["available_templates"]==0 for x in subset),
            "originals_with_some_training_template_original_proof":sum(
                x["fully_original_VC_proven_templates"]>0 for x in subset),
            "originals_with_uncertain_template_proof":sum(
                x["unknown_or_error_templates"]>0 for x in subset),
            "all_templates_refuted_after_strict_vcs":sum(
                x["status"]=="ALL_CANDIDATES_ORIGINAL_VC_REFUTED" for x in subset),
            "first_trained_neural_TOP3_original_proofs":sum(
                x["actual_first_learned_top3"] for x in subset),
            "first_strong_classical_original_proofs":sum(
                x["first_model_classical_spacer"]=="unsat" for x in subset),
        }
        old=prior["all_model_eval_cases"][label]
        if old["evaluated_original_count"]!=buckets[label]["originals"] or old["trained_TOP3_certified"]!=buckets[label]["first_trained_neural_TOP3_original_proofs"]:
            raise ValueError("PRIOR_FULL_ORIGINAL_PAIRING_MISMATCH")
    return {
        "study":"Q3P2_FROZEN_FIRST_11_TRAINING_TEMPLATES_ALL_ORIGINAL_VC_ORACLE_AUDIT",
        "status":"COMPLETE_ONLY_ORIGINAL_SOURCE_FINITE_REPERTOIRE_VERDICT",
        "first_model_first_receipt_sha256":Q3P_FIRST_JSON_SHA,
        "first_original_candidate_count":11,
        "first_original_source_count":len(sources),
        "posthoc_hard_no_training_update":True,
        "unseen_group_labels_used_for_training":False,
        "all_frozen_candidates_checked":True,
        "test_source_origin_disjoint":True,
        "q3f_challenge_targets_unopened":True,
        "new_math_operator_created":False,
        "global_q1_q7":"OPEN",
        "per_split_outcomes":buckets,
        "candidate_original_three_vc_status_counts":dict(statuses),
        "training_template_reconstruction_ms":round((time.perf_counter_ns()-t0)/1e6,3),
        "all_original_proof_receipts":results
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--first-q3p",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=run(a.root,a.first_q3p)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print("Q3P2_FROZEN_ALL_REAL_TRAINED_TEMPLATES",result["per_split_outcomes"])
    print("Q3P2_ORIGINAL_VC_VERDICTS",result["candidate_original_three_vc_status_counts"])
    print("Q3P2_GLOBAL",result["global_q1_q7"])
