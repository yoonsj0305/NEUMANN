"""Sound posthoc source-published Post proof: k=1..3, optional fully
source-inductive least affine GF2 strengthening. ALL historical sources kept.

For multi-step formulas, each transition's auxiliary nondeterministic globals
are independently alpha-renamed. No accidentally shared source nondet globals
across time. Original source bytes and native/typed parity dual-certified.
Classical zero-training proof; not a learned-Q3 claim.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import z3

from research.evidence.q3_exact_GF2_all_arity_20261021.first_source_64_observation_exact_nullspace import (
    blob, sha, sexprs, compile_typed_original, compile_independent_native, dual, elapsed
)
from research.evidence.q3_exact_GF2_all_arity_20261021.dragon2_exact_affine_inductive_fixpoint import (
    converge, kernel_expr
)

UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
MAX_K=3
TIMEOUT_SEC=8


def instances(original, n_states, k):
    now,nxt=original["now"],original["next"]
    all_vars=z3.z3util.get_vars(z3.And(original["pre"],original["trans"],original["post"]))
    state_names={str(v) for v in now+nxt}
    extra=[v for v in all_vars if str(v) not in state_names]
    states=[
        [z3.Const(f"q3_t{t}_s{j}",v.sort()) for j,v in enumerate(now)]
        for t in range(k+1)
    ]
    def inst(expr,t):
        items=list(zip(now,states[t]))+list(zip(nxt,states[min(t+1,k)]))
        items += [(v,z3.Const(f"q3_aux_t{t}_v{j}",v.sort()))
                  for j,v in enumerate(extra)]
        return z3.substitute(expr,*items)
    pre=inst(original["pre"],0)
    trans=[inst(original["trans"],t) for t in range(k)]
    posts=[inst(original["post"],t) for t in range(k+1)]
    return pre,trans,posts,states,inst,len(extra)


def check_property(original, inv, k, use_affine):
    pre,trans,posts,states,inst,extra_count=instances(original,len(original["now"]),k)
    # For every reachable original prefix of length <=k-1 verify Post.
    base=[]
    for t in range(k):
        witness=z3.And(pre,*trans[:t],z3.Not(posts[t]))
        proof=dual(witness,"unsat",TIMEOUT_SEC)
        base.append({"step":t,"dual":proof})
        if not proof["dual_pass"]:
            return {"k":k,"uses_affine":use_affine,"status":"BASE_NOT_PROVED",
                    "bases":base,"source_aux_globals_renamed_per_step":extra_count}
    strengthened=[
        z3.And(posts[t],inst(inv,t)) if use_affine else posts[t]
        for t in range(k)
    ]
    step=dual(z3.And(*strengthened,*trans,z3.Not(posts[k])),"unsat",TIMEOUT_SEC)
    return {"k":k,"uses_affine":use_affine,
            "status":"ORIGINAL_PUBLISHED_POST_K_INDUCTIVE_DUAL_PROVED" if step["dual_pass"] else "K_INDUCTION_STEP_NOT_PROVED",
            "bases":base,"step":step,
            "source_aux_globals_renamed_per_step":extra_count,
            "soundness_note":"All k base cases and k-step induction UNSAT over same unmodified source Pre/Trans/Post; independent transition nonstate extras per step; optional affine conjunction fully original 2VC proved beforehand."}


def check_case(root,entry):
    start=time.perf_counter_ns()
    row={"source":entry["path"],"git_blob":entry["git_blob"],
         "status":"ABSTAIN","global_Q3":"OPEN","actual_full_original_Post_proven":False}
    try:
        raw=(root/entry["path"]).read_bytes()
        if blob(raw)!=entry["git_blob"] or len(raw)!=entry["bytes"]:
            raise RuntimeError("SOURCE_BYTES_CHANGED")
        row["original_sha256"]=sha(raw)
        parsed=compile_typed_original(sexprs(raw))
        native=compile_independent_native(sexprs(raw),parsed)
        row["original_native_typed_semantic_dual"]={
            q:dual(z3.Xor(parsed[q],native[q]),"unsat",TIMEOUT_SEC)
            for q in ("pre","trans","post")
        }
        if not all(p["dual_pass"] for p in row["original_native_typed_semantic_dual"].values()):
            raise RuntimeError("ORIGINAL_NATIVE_SEMANTIC_MISMATCH")
        original={**parsed,**native}
        row["source_pre_sat"]=dual(original["pre"],"sat",TIMEOUT_SEC)
        if not row["source_pre_sat"]["dual_pass"]:
            raise RuntimeError("PRE_NONVACUITY_NOT_DUAL_CONFIRMED")
        used={str(x) for x in z3.z3util.get_vars(native["post"])}
        positions=[i for i,(_,typ) in enumerate(parsed["states"])
                  if typ=="Bool" and str(parsed["now"][i]) not in used]
        row["source_goal_excluded_bool_indices"]=positions
        affine=None
        if 1<=len(positions)<=32:
            raw_result=converge(original["pre"],original["trans"],
                    original["now"],original["next"],positions,30000)
            row["source_affine_fixedpoint_status"]=raw_result["status"]
            if raw_result["status"]=="Z3_EXACT_LEAST_AFFINE_FIXEDPOINT_OBTAINED":
                affine=kernel_expr(raw_result["complete_affine_GF2_kernel_vectors"],
                                   original["now"],positions)
                invp=kernel_expr(raw_result["complete_affine_GF2_kernel_vectors"],
                                 original["next"],positions)
                row["affine_original_inductiveness_2VC"]={
                    "base":dual(z3.And(original["pre"],z3.Not(affine)),"unsat",TIMEOUT_SEC),
                    "step":dual(z3.And(affine,original["trans"],z3.Not(invp)),"unsat",TIMEOUT_SEC),
                }
                if not all(x["dual_pass"] for x in row["affine_original_inductiveness_2VC"].values()):
                    affine=None
        row["proof_trials"]=[]
        # Require explicit and independent 2VC before using affine strengthening.
        for k in range(1,MAX_K+1):
            for use_affine in (False,True):
                if use_affine and affine is None:continue
                trial=check_property(original,affine if use_affine else z3.BoolVal(True),k,use_affine)
                row["proof_trials"].append(trial)
                if trial["status"]=="ORIGINAL_PUBLISHED_POST_K_INDUCTIVE_DUAL_PROVED":
                    row["status"]="CERTIFIED_FULL_PUBLISHED_SOURCE_SAFETY_BY_K_INDUCTION"
                    row["actual_full_original_Post_proven"]=True
                    row["first_full_success_k"]=k
                    row["first_full_success_affine_strengthening"]=use_affine
                    return row
        row["status"]="ABSTAIN_POST_PROPERTY_NOT_K_INDUCTIVE_UP_TO_K3"
    except Exception as e:
        row["error"]=type(e).__name__+":"+str(e)[:300]
        row["status"]="ABSTAIN_EXCEPTION"
    finally:
        row["wall_ms"]=elapsed(start)
        print("ORIGINAL_PUBLISHED_POST_K_INDUCTIVE",row["source"],
             row["status"],"k",row.get("first_full_success_k"),
             "AFFINE",row.get("first_full_success_affine_strengthening"),
             "ERROR",row.get("error"),flush=True)
    return row


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--freeze",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    meta=json.loads(args.freeze.read_text())
    if len(meta["source_targets"])!=4 or meta["upstream_commit"]!=UPSTREAM:
        raise RuntimeError("PREGISTERED_FOUR_COHORT_CHANGED")
    rows=[check_case(args.root,e) for e in meta["source_targets"]]
    result={
        "schema":"neumann.q3.published_Post.original_k_induction_original4.v1",
        "posthoc_already_opened_source":True,
        "source_preopen_original_freeze":"8e6efc5b5a6f637ac6b92fbb459616e30ce97072",
        "origins_all_retained":len(rows)==4,
        "original_published_safety_3VC_or_k_induction_pass":sum(r["actual_full_original_Post_proven"] for r in rows),
        "neural_training":0,"neural_inference":0,"paid_API":0,
        "global_Q3":"OPEN","Q4_full":"OPEN","full_neural_novelty":"NOT_DEMONSTRATED",
        "results":rows,
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("K_INDUCTION_FULL_ORIGINAL_PUBLISHED_SAFETY",result["original_published_safety_3VC_or_k_induction_pass"],"/4")
    print("GLOBAL_Q3",result["global_Q3"])
if __name__=="__main__":
    main()
