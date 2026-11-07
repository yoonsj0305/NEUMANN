"""Q6 source-frozen post-FIRST causal ablation: withhold str.at from proposer.

The previously successful inventor is sealed byte-for-byte at
Git blob 66e76f829e2245b34327b609dc62e6075e15e317.
No change to source proof, target semantics, observer AST generator, or
independent Z3 verifier. Disable one available operator HEAD at the
interface, then ask if the general grammar can discover an equivalent
previously unselected representation via another head.

This uses the SAME development-exposed #685 String task. It is NOT an
independent-author problem, never an unrestricted Q3/Q6 generalization gate.
"""
from __future__ import annotations
from hashlib import sha1
import argparse
import json
from pathlib import Path
import time

from research.q6.auto_structural_mapping_proof_memory import (
    heads_from_existing_target_semantics,
    select_observation_without_reference_oracle,
    proof_contracts,check_smt,digest,
    ObservationTerm,
)

SOURCE_BLOB="66e76f829e2245b34327b609dc62e6075e15e317"
SCHEMA="neumann.q6.alpha-head-withheld-frozen-proposer-ablation.v1"


def gitblob(path:Path):
    data=path.read_bytes()
    return sha1(b"blob "+str(len(data)).encode()+b"\x00"+data).hexdigest()


def run(out:Path):
    inventor=Path(__file__).with_name("auto_structural_mapping_proof_memory.py")
    if gitblob(inventor)!=SOURCE_BLOB:
        raise ValueError("PROPOSER_WAS_CHANGED_POSTFIRST")
    if out.exists():raise ValueError("NO_OVERWRITE_ABLATION_FIRST")
    out.mkdir(parents=True)
    t=time.perf_counter_ns()
    available=heads_from_existing_target_semantics()
    assert "str.at" in available and "str.substr" in available
    withheld=[h for h in available if h!="str.at"]
    candidates,audit,survivors=select_observation_without_reference_oracle(withheld)
    tests=[]
    for term in survivors:
        obligations=proof_contracts(term)
        checks={}
        for name,(expected,script) in obligations.items():
            checks[name]=check_smt(script,expected,timeout_s=15)
            (out/(name+".smt2")).write_text(script+"\n(check-sat)\n")
        tests.append({"generated_AST":term.ast(),
                      "frozen_before_verifier_sha256":digest(term.ast()),
                      "checks":checks,
                      "allproofs":all(c["pass"] for c in checks.values())})
    # Formal wrong-index hard negative using the SAME surviving String
    # primitive. Failing alternatives are not silently renamed successes.
    decoy=ObservationTerm("str.substr","j+1",1)
    expected,wrongbody=proof_contracts(decoy)["INVENTED_ALPHA_COMMUTING"]
    wrong=check_smt(wrongbody,"sat",timeout_s=8)
    success=(len(survivors)>=1 and all(
        item["generated_AST"][1]!="str.at" for item in tests) and
        any(x["allproofs"] for x in tests) and wrong["pass"])
    report={
        "schema":SCHEMA,
        "original_first_actions_run":42345742856,
        "postfirst_diagnostic_same_originals":True,
        "proposer_original_source_blob":SOURCE_BLOB,
        "frozen_proposer_unchanged":True,
        "ablated_head":"str.at",
        "abi_verifier_target_semantics_unchanged":True,
        "candidate_proposer_heads":withheld,
        "candidates_after_ablation":len(candidates),
        "candidate_probe_audit":audit,
        "candidates_surviving":len(survivors),
        "generated_alternative_programs":tests,
        "wrong_same_primitive_index_proof":wrong,
        "scoped_ablation_pass":success,
        "elapsed_ms":round((time.perf_counter_ns()-t)/1e6,3),
        "Q3_GLOBAL":"OPEN","Q4_GLOBAL":"OPEN","Q6_GLOBAL":"OPEN",
    }
    (out/"FIRST.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("WITHHOLD_STR_AT_ABLATION",json.dumps({
        "candidates":len(candidates),"survivors":len(survivors),
        "verified_alternative_ASTS":[x["generated_AST"]
                                     for x in tests if x["allproofs"]],
        "wrong_index_counterexample":wrong["observed"],
        "scoped_ablation_pass":success,
        "elapsed_ms":report["elapsed_ms"],
    },sort_keys=True),flush=True)
    if not success:
        raise RuntimeError("FROZEN_WITHHELD_HEAD_GENERALIZATION_FAILED")
    return report


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    run(ap.parse_args().out)
