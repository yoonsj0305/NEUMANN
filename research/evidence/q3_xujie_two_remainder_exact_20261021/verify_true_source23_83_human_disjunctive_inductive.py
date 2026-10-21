"""Posthoc human hypothesis proofs of two xujie original program abstentions.

THIS IS NOT MACHINE-LEARNED DISCOVERY. Original source SHA locked before
any original first opening in PR408. Humans derived:
 23.c.sl: i + 2*j == 41 and j >= 13
 83.c.sl: x < 0 or y > 0
On authentic unchanged native source Pre/Trans/Post, independent Z3 and
cvc5 must prove all 3 complete induction VCs. A weaker candidate MUST FAIL;
no replacement of first-blind learned history; do not count this as model Q3.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import z3
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    prepare, verified_3vc,dual,DUAL_S
)
TARGETS={
 "lib/Inv_Track/xujie_code2inv/23.c.sl":
     {"sha":"0f49b7a857b8a12cce0c3d17c69197c1aa127448",
      "states":["i","j","i_0","i_1","i_2","i_3","j_0","j_1","j_2","j_3"]},
 "lib/Inv_Track/xujie_code2inv/83.c.sl":
     {"sha":"364ed512df08efcdd3877c56f7743766d325ef49",
      "states":["x","y","x_0","x_1","x_2","x_3","y_0","y_1","y_2"]}}
def source_proof(root,item):
    start=time.perf_counter_ns()
    out={"path":item["path"],"original_git_blob":item["git_blob"],
         "human_posthoc_not_learned":True,"status":"ABSTAIN"}
    try:
        raw,src,native,parity=prepare(root,item)
        out["real_original_full_source_Pre_Trans_Post_native_parity"]=parity
        current=[n for n,k in src["states"]]
        if current!=TARGETS[item["path"]]["states"]:
            raise RuntimeError("UNEXPECTED_SOURCE_ORIGINAL_STATE_NAMES_STOP")
        vals={name:sym for name,sym in zip(current,src["now"])}
        if item["path"].endswith("23.c.sl"):
            i,j=vals["i"],vals["j"]
            candidate=z3.And(i+2*j==41,j>=13)
            ablate=z3.And(j>=13)
            error_goal=z3.And(ablate,z3.Not(native["post"]))
            # This deliberately weak nonoriginal invariant cannot prove Post;
            # include phase alias equalities to build an actual model if needed.
            s=z3.Solver();s.add(error_goal)
            if s.check()!=z3.sat:
                raise RuntimeError("WEAK23_GOAL_NOT_SAT_UNEXPECTED")
            negative=dual(error_goal,"sat",DUAL_S)
            out["synthetic_weakened_invariant_not_good_enough_goal_dual_SAT"]=negative
        elif item["path"].endswith("83.c.sl"):
            x,y=vals["x"],vals["y"]
            candidate=z3.Or(x<0,y>0)
            ablate=x<0
            weak_next=z3.substitute(ablate,*list(zip(src["now"],src["next"])))
            negative=dual(z3.And(ablate,native["trans"],z3.Not(weak_next)),"sat",DUAL_S)
            out["synthetic_weakened_single_phase_noninduction_dual_SAT"]=negative
        else:
            raise RuntimeError("NOT_EXACTLY_PREREGISTERED_TWO")
        safe,cert=verified_3vc(src,native,candidate)
        out["human_candidate_source_mathematical_AST"]=candidate.sexpr()
        out["human_candidate_SHA256"]=hashlib.sha256(candidate.sexpr().encode()).hexdigest()
        out["authentic_original_independent_Z3_cvc5_init_consecution_goal_receipts"]=cert
        out["full_original_safe_inductive_source_proof"]=bool(safe)
        out["negative_weak_control_genuine_source_proof_fails"]=bool(negative["dual_pass"])
        out["status"]=("COMPLETE_POSTHOC_HUMAN_INVARIANT_PROVED_ORIGINAL_SAFE"
                      if safe and negative["dual_pass"]
                      else "HOLD_HUMAN_CANDIDATE_UNPROVEN")
    except Exception as e:
        out["status"]="ABSTAIN_SOURCE_OR_SOLVER"
        out["error"]=type(e).__name__+":"+str(e)[:420]
    out["full_source_authentication_and_all_induction_proof_ms"]=(time.perf_counter_ns()-start)/1e6
    print("ORIGINAL_REAL_TWO_REMAINDER",item["path"],out["status"],
          "FULL_NATIVE_DUAL_3VC",out.get("full_original_safe_inductive_source_proof"),
          "NEGATIVE",out.get("negative_weak_control_genuine_source_proof_fails"),
          "ERROR",out.get("error"),flush=True)
    return out
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","out"):p.add_argument("--"+k,required=True)
    args=p.parse_args()
    q=json.loads(Path(args.freeze).read_text())
    assert q["schema"]=="neumann.q3.20261021.unseen_cross_family_xujie_code2inv_12_original_SHA_metadata_only.v1"
    lookup={z["path"]:z for z in q["cases"]}
    assert len(lookup)==12
    cases=[]
    for key,tgt in TARGETS.items():
        assert key in lookup and lookup[key]["git_blob"]==tgt["sha"]
        cases.append(lookup[key])
    rows=[source_proof(Path(args.root),v) for v in cases]
    report={
      "schema":"neumann.q3.xujie_original2_human_posthoc_full_native_inductive_safe_v1",
      "these_source_bodies_already_opened_PR408":True,
      "genuine_originals":2,
      "human_discovered_not_model_inferred":True,
      "safe_both_independent_Z3_cvc5_all3VC":sum(r.get("full_original_safe_inductive_source_proof",False) and
                                                r.get("negative_weak_control_genuine_source_proof_fails",False)
                                                for r in rows),
      "old_frozen_model_OOD_12_SAFEs":9,
      "old_frozen_original_one_Z3_cvc5_UNSAFE":1,
      "original12_truth_partition_only_if_both_safe_human":True,
      "DO_NOT_add_human_discovery_to_learned_Q3":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
      "two_posthoc_source_certificates":rows
    }
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("ORIGINAL_XUJIE_TWO_HUMAN_POSTHOC_ORIGINAL_SAFE",report["safe_both_independent_Z3_cvc5_all3VC"])
    print("GLOBAL_MODEL_Q3_OPEN")
if __name__=="__main__":main()
