"""Honest one-step UNSAFE source certificate for the previously frozen
fib_07.sl; keep first Q4 5/6 proof receipt unchanged.

Source exact original Pre allows n>=0, original Trans leaves next n!
UNCONSTRAINED, and original Post checks sum a+b=3*n when i>=n.
A satisfying native Pre/Trans/NotPost reachable trace is a mathematical
refutation of original safety, NOT a failure of proof ability.
"""
import argparse,json
from pathlib import Path
import z3

from research.evidence.q3_exact_GF2_all_arity_20261021.first_source_64_observation_exact_nullspace import (
    blob,sha,sexprs,compile_typed_original,compile_independent_native,dual
)
SOURCE="lib/Inv_Track/from_2018/fib_07.sl"
GIT_BLOB="d078734e83a870d7b95a68bc7a947cf85ff944d8"
# State order preserved by original synth-inv ((i Int) (n Int) (a Int) (b Int))
PRE=(0,1,0,0)
POST=(1,0,1,2)

def certificate(root):
    raw=(root/SOURCE).read_bytes()
    if blob(raw)!=GIT_BLOB:
        raise RuntimeError("FIRST_FROZEN_ORIGINAL_SOURCE_GIT_BLOB_CHANGED")
    parsed=compile_typed_original(sexprs(raw))
    native=compile_independent_native(sexprs(raw),parsed)
    if [(name,typ) for name,typ in parsed["states"]] !=[
      ("i","Int"),("n","Int"),("a","Int"),("b","Int")]:
        raise RuntimeError("ORIGINAL_STATE_SIGNATURE_NOT_EXPECTED")
    parity={
      kind:dual(z3.Xor(parsed[kind],native[kind]),"unsat",10)
      for kind in ("pre","trans","post")
    }
    if not all(x["dual_pass"] for x in parity.values()):
        raise RuntimeError("ORIGINAL_NATIVE_TYPED_SEMANTICS_NOT_EQUAL")
    ground=z3.And(*[
        v==z3.IntVal(k) for v,k in zip(parsed["now"],PRE)
    ],*[
        v==z3.IntVal(k) for v,k in zip(parsed["next"],POST)
    ])
    proofs={
        "actual_original_initial_source":dual(
            z3.And(ground,native["pre"]),"sat",12),
        "actual_original_true_transition":dual(
            z3.And(ground,native["trans"]),"sat",12),
        "actual_original_published_post_violated":dual(
            z3.And(ground,z3.Not(
                z3.substitute(native["post"],*list(zip(parsed["now"],parsed["next"])))
            )),"sat",12),
        "whole_single_reachable_path_source":dual(
            z3.And(ground,native["pre"],native["trans"],
                z3.Not(z3.substitute(native["post"],*list(zip(parsed["now"],parsed["next"]))))),
            "sat",12),
    }
    is_bad=all(x["dual_pass"] for x in proofs.values())
    record={
       "source":SOURCE,
       "frozen_original_git_blob":GIT_BLOB,
       "true_original_sha256":sha(raw),
       "source_native_typed_semantic_parity":parity,
       "original_state_sequence_0":{"i":PRE[0],"n":PRE[1],"a":PRE[2],"b":PRE[3]},
       "original_state_sequence_1":{"i":POST[0],"n":POST[1],"a":POST[2],"b":POST[3]},
       "why_counterexample_valid":"Original source Trans does not constrain n!; choosing n'=0 is source-permitted. At reached i'=1>=n'=0, published Post requires a'+b'=3*n' but 3 != 0.",
       "source_original_published_safety_one_step_dual_refuted":is_bad,
       "actual_original_ground_witness_independent_Z3_and_cvc5":proofs,
       "status":"TRUE_ORIGINAL_ONE_STEP_UNSAFE_IN_TWO_SOLVERS" if is_bad else "ABSTAIN_NOT_DUAL_REPRODUCED",
       "no_fabricated_safety_proof":True,
       "historical_first_5_6_safe_proof_preserved":True,
       "global_Q3":"OPEN","global_Q4":"OPEN",
    }
    return record

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    output={
       "schema":"neumann.q4.first_real_original_fib07_one_step_unsafety_dual.v1",
       "posthoc_after_true_source_first_PDR_SAT_result":True,
       "source_first_pre_content_identity_commit":"63f8ca99b8f9f00aa2bd562226d78641e7e9889c",
       "full_original":certificate(args.root),
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(output,indent=2,sort_keys=True)+"\n")
    r=output["full_original"]
    print("FIRST_ORIGINAL_FIB07_TRUE_DUAL_UNSAFE",r["source_original_published_safety_one_step_dual_refuted"])
    print("ACTUAL_UNMODIFIED_PROGRAM_STATUS",r["status"])
if __name__=="__main__":
    main()
