"""Source-native exact minimal information profile for all twelve original
programs. All were already opened in PR412; no blind or learned claim.

For each original, seek smallest *arbitrary* subset S of current state vars
whose observation can distinguish every source Pre and every one-step
successor from any source NotPost state. Enumerate ALL smaller feature
subsets, independently certify Z3+cvc5 SAT aliases for each, and certify
winner UNSAT in both. If no subset <=3 exists, preserve INCOMPLETE.
This is necessary information only, NOT full inductive invariant sufficiency.
"""
from __future__ import annotations
import argparse,itertools,json,math,time
from pathlib import Path
import z3
from research.evidence.q3_gater_relational_mixed_20261020.first_actual_nondet_and_branch_originals import (
    blob,sexprs,compile_typed_original,compile_independent_native,dual
)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import DUAL_S

def millis(t):return (time.perf_counter_ns()-t)/1e6
def once(root,item):
    start=time.perf_counter_ns()
    out={"path":item["path"],"git_blob":item["git_blob"],"status":"ABSTAIN"}
    try:
        b=(root/item["path"]).read_bytes()
        if len(b)!=item["bytes"] or blob(b)!=item["git_blob"]:
            raise RuntimeError("REAL_ORIGINAL_GIT_IDENTITY_MISMATCH")
        src=compile_typed_original(sexprs(b))
        native=compile_independent_native(sexprs(b),src)
        parity={k:dual(z3.Xor(src[k],native[k]),"unsat",DUAL_S)
                for k in ("pre","trans","post")}
        if not all(z["dual_pass"] for z in parity.values()):
            raise RuntimeError("SOURCE_NATIVE_AST_PARITY_MISMATCH")
        out["independent_genuine_source_PreTransPost_equivalence"]=parity
        n=len(src["now"])
        shadow=[z3.Const("independent_shadow_"+str(i),x.sort())
                for i,x in enumerate(src["now"])]
        bad=z3.substitute(z3.Not(native["post"]),*list(zip(src["now"],shadow)))
        badnext=z3.substitute(z3.Not(native["post"]),
                              *list(zip(src["now"],src["next"])))
        unsafe0=z3.And(native["pre"],z3.Not(native["post"]))
        unsafe1=z3.And(native["pre"],native["trans"],badnext)
        def quick(phi):
            s=z3.Solver();s.set(timeout=3500);s.add(phi)
            r=s.check()
            if r==z3.unknown:raise RuntimeError("REAL_SOURCE_SMTCAP_UNKNOWN")
            return str(r)
        check_unsafe0=quick(unsafe0);check_unsafe1=quick(unsafe1)
        if check_unsafe0=="sat" or check_unsafe1=="sat":
            which=unsafe0 if check_unsafe0=="sat" else unsafe1
            evidence=dual(which,"sat",DUAL_S)
            if not evidence.get("dual_pass"):raise RuntimeError("UNSAFE_NOT_DUAL_CERTIFIED")
            out["status"]="ORIGINAL_UNSAFE_WITH_ZERO_ONE_STEP_WITNESS"
            out["real_native_UNSAFE_Z3_cvc5"]=evidence
            return out
        checks=[]
        def projected(sub):
            return z3.Or(
                z3.And(native["pre"],bad,
                       *(src["now"][i]==shadow[i] for i in sub)),
                z3.And(native["pre"],native["trans"],bad,
                       *(src["next"][i]==shadow[i] for i in sub)))
        winner=None;tried=[]
        for size in range(min(n,3)+1):
            for s in itertools.combinations(range(n),size):
                v=quick(projected(s))
                tried.append((s,v))
                if v=="unsat":
                    winner=s;break
            if winner is not None:break
        out["original_state_variable_count"]=n
        out["exact_Z3_candidate_feature_subsets_searched"]=len(tried)
        if winner is None:
            out["status"]="NOT_FOUND_WITH_AT_MOST_THREE_FEATURES_NO_FALSE_MINIMUM"
            return out
        # All cardinalities BELOW winner were exhaustively explored.
        smaller=[t for t in tried if len(t[0])<len(winner)]
        if len(smaller)!=sum(math.comb(n,k) for k in range(len(winner))):
            raise RuntimeError("EXHAUSTIVE_MINIMUM_SEARCH_NOT_COMPLETE")
        proof_small=[]
        for subset,res in smaller:
            if res!="sat":raise RuntimeError("SUBMINIMAL_ORIGINAL_ALIAS_NOT_SAT")
            ev=dual(projected(subset),"sat",DUAL_S)
            if not ev.get("dual_pass"):raise RuntimeError("SUBMINIMAL_ALIAS_NOT_DUAL")
            proof_small.append({"indices":list(subset),"dual_original_sat":ev})
        sufficient=dual(projected(winner),"unsat",DUAL_S)
        if not sufficient.get("dual_pass"):
            raise RuntimeError("SEMANTIC_MINIMUM_UNSAT_NOT_DUAL")
        out.update({
            "status":"MINIMUM_ORIGINAL_SOURCE_INFO_PROVED_BY_BOTH_SOLVERS",
            "minimal_cardinality_for_0_1_step_versus_NotPost":len(winner),
            "one_minimal_original_feature_indices":list(winner),
            "one_minimal_original_feature_names":[src["states"][i][0] for i in winner],
            "all_smaller_feature_combinations_dual_SAT":len(proof_small),
            "all_strictly_smaller_subsets_proved_insufficient":True,
            "selected_projection_true_source_dual_UNSAT":sufficient,
            "smaller_original_alias_proofs":proof_small,
            "original_initial_and_first_step_unsafe_refuted_Z3":[check_unsafe0,check_unsafe1],
            "NOT_proof_complete_inductive_source_safety":True
        })
    except Exception as e:
        out["status"]="ABSTAIN_NATIVE_SOURCE_OR_PROOF"
        out["error"]=type(e).__name__+":"+str(e)[:370]
    finally:
        out["full_real_source_information_analysis_ms"]=millis(start)
        print("ORIGINAL12_EXACT_MIN_STATE",out["path"].split("/")[-1],
              out["status"],"K",out.get("minimal_cardinality_for_0_1_step_versus_NotPost"),
              "CHOICE",out.get("one_minimal_original_feature_indices"),
              "DUAL_SMALLER",out.get("all_smaller_feature_combinations_dual_SAT"),
              "ERROR",out.get("error"),flush=True)
    return out
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    q=json.loads(Path(a.freeze).read_text())
    assert q["schema"]=="neumann.q3.train_BOOLEAN_DNF_first12_unopened_xujie_SHA.v1"
    assert len(q["cases"])==12 and len({x["git_blob"] for x in q["cases"]})==12
    rows=[once(Path(a.root),x) for x in q["cases"]]
    proven=[x for x in rows if x["status"]=="MINIMUM_ORIGINAL_SOURCE_INFO_PROVED_BY_BOTH_SOLVERS"]
    report={
        "schema":"neumann.q3.12_real_original_exact_minimal_0_1_step_information_profile.v1",
        "original_SHA_frozen_before_first_read_in_prior_PR412":True,
        "study_is_posthoc_original_source_bodies_already_opened":True,
        "original_source_count":len(rows),
        "exact_minimum_feature_count_certified_originals":len(proven),
        "minimum_feature_cardinality_histogram":{
            str(i):sum(x["minimal_cardinality_for_0_1_step_versus_NotPost"]==i for x in proven)
            for i in range(4)},
        "total_subminimum_independent_SAT_certificates":
            sum(x["all_smaller_feature_combinations_dual_SAT"] for x in proven),
        "genuine_unsafe_originals_with_dual_counterexample":
            sum(x["status"]=="ORIGINAL_UNSAFE_WITH_ZERO_ONE_STEP_WITNESS" for x in rows),
        "unresolved_or_abstained_cases":
            12-len(proven)-sum(x["status"]=="ORIGINAL_UNSAFE_WITH_ZERO_ONE_STEP_WITNESS" for x in rows),
        "maximum_cardinality_search_attempted":3,
        "bounded_necessary_information_NOT_inductive_sufficiency":True,
        "no_training_claim_or_weights":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "all_originals":rows}
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    for k in ("exact_minimum_feature_count_certified_originals",
              "minimum_feature_cardinality_histogram",
              "total_subminimum_independent_SAT_certificates",
              "genuine_unsafe_originals_with_dual_counterexample",
              "unresolved_or_abstained_cases"):
        print("NEUMANN_ACTUAL_SOURCE12_MINIMAL_INFORMATION",k,report[k],flush=True)
    print("Q3_GLOBAL_OPEN",flush=True)
if __name__=="__main__":main()
