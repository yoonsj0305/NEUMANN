"""FGSR science-admission preflight only. Never promotes Q1–Q7.
No proof verification/provider authentication is performed here.
"""
import argparse, json
from pathlib import Path

ROLES=("strong_classical","without_learning","neumann")
def assess(x):
    b=[]
    def req(ok,why):
        if not ok:b.append(why)
    if not isinstance(x,dict):return {"status":"BLOCKED_SCHEMA","reasons":["NOT_OBJECT"],"q1_q7":"OPEN"}
    o=x.get("original",{})
    l=x.get("learned_semantics",{})
    arms=x.get("arms",{})
    if not isinstance(o,dict):o={}
    if not isinstance(l,dict):l={}
    if not isinstance(arms,dict):arms={}
    source=o.get("sha256","")
    goal=o.get("goal_hash","")
    hashok=lambda s: type(s) is str and len(s)==64 and all(c in "0123456789abcdef" for c in s)
    req(x.get("contract")=="NEUMANN_FGSR_CAUSAL_V1","BAD_CONTRACT")
    req(hashok(source) and hashok(goal),"ORIGINAL_OR_GOAL_UNBOUND")
    req(o.get("source_group_disjoint") is True,"SAME_OR_OPENED_SOURCE_FAMILY")
    req(o.get("opened_during_model_design") is False,"MODEL_EXPOSED_TO_TARGET")
    req(o.get("provenance_audited") is True,"NO_SOURCE_PROVENANCE_AUDIT")
    n=l.get("actual_train_updates",0)
    req(type(n) is int and n>0,"NO_ACTUAL_TRAINED_SEMANTIC_MODEL")
    req(l.get("frozen_before_target_access") is True,"MODEL_NOT_FROZEN")
    req(l.get("full_source_and_goal_input") is True,"NO_GOAL_CONDITIONING")
    req(l.get("unprovided_relation_semantics") is True,"NO_NEW_SEMANTIC_RELATION")
    req(l.get("complete_typed_relational_output") is True,"NO_TYPED_COMPLETE_RELATION")
    req(l.get("model_emitted_semantics_not_compiler_inserted") is True,"NOT_MODEL_SEMANTICS")
    req(l.get("holdout_absent_from_training") is True,"TRAIN_TARGET_LEAKAGE")
    req(hashok(l.get("checkpoint_sha256")) and hashok(l.get("decoder_sha256")),"UNBOUND_MODEL_OR_DECODER")
    for role in ROLES:
        a=arms.get(role)
        if not isinstance(a,dict):
            b.append("MISSING_"+role.upper());continue
        req(a.get("original_sha256")==source and a.get("goal_hash")==goal,"MISMATCH_"+role.upper())
    if all(isinstance(arms.get(r),dict) for r in ROLES):
        c=arms["strong_classical"];a=arms["without_learning"];n=arms["neumann"]
        req(c.get("actual_run_completed") is True and c.get("verified") is not True,"CLASSICAL_NOT_EVALUATED_OR_SOLVED")
        req(c.get("matched_original_tool_budget") is True and c.get("matched_source_information") is True,"CLASSICAL_UNFAIR")
        req(a.get("actual_run_completed") is True and a.get("verified") is not True,"ABLATION_NOT_EVALUATED_OR_SOLVED")
        req(n.get("original_clauses_all_unsat") is True and n.get("original_proof_independently_replayed") is True,"NOT_FULL_ORIGINAL_PROOF")
        req(n.get("negative_controls_pass") is True and hashok(n.get("original_verifier_sha256")),"NO_PROOF_FALSIFICATION")
    small=arms.get("small") if isinstance(arms.get("small"),dict) else {}
    front=arms.get("frontier") if isinstance(arms.get("frontier"),dict) else {}
    q7=(small.get("run_completed") is True and small.get("verified") is False
        and front.get("verified") is True and front.get("provider_attested") is True
        and small.get("original_sha256")==source and front.get("original_sha256")==source
        and small.get("goal_hash")==goal and front.get("goal_hash")==goal)
    return {"status":"BLOCKED_CAUSAL_ADMISSION" if b else "ELIGIBLE_FOR_INDEPENDENT_REVIEW_NOT_PROVEN",
            "reasons":sorted(set(b)),"q7_gap":"REVIEW_ONLY" if q7 else "BLOCKED_PROVIDER_OR_SMALL",
            "q1_q7":"OPEN","proof_authority":"NEVER: external audit needed"}
def main():
    p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args(); cases=json.loads(a.input.read_text())["cases"]
    if not isinstance(cases,list) or not cases:raise ValueError("NO_CASES")
    verdict={"q1_q7":"OPEN","neural_calls":0,"results":[{"case":x.get("case_id","UNKNOWN"),**assess(x)} for x in cases]}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(verdict,indent=2)+"\n")
    print("RESULT",[(x["case"],x["status"],len(x["reasons"])) for x in verdict["results"]])
if __name__=="__main__":main()
