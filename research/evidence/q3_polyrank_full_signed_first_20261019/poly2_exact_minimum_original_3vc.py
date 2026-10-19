"""Posthoc exact two-atom PolyRank original Z3 + independent cvc5 proof.

Uses unchanged genuine source/parser/checker and separately replays the exhaustive
37-subset sympy result. Not a new blind/learned result; global Q1-Q7 stay open.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import time
from pathlib import Path

import z3

from experiments.q3_source_prove import (
    sexprs, extract_mixed_original, native_original_relations,
    check_parity, check_formula, source_proof,
)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate
from research.evidence.q3_polyrank_full_signed_first_20261019.poly2_auto_minimal_exact import run as exact_minimum

PINNED_GIT_BLOB = "17448225fffad0cef48634b9d68f4f9193d616d8"
PINNED_SHA256 = "2a8a874b4f0861cb8219059dfc9572c6f02a827e80d0c0cc583c7f13c251eb7d"
SOURCE = "benchmarks/LIA/2005.ICALP_PolyRank/poly2.sl"
ACCEPTED = "CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5"

def gitblob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def study(path):
    start = time.perf_counter_ns()
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != PINNED_SHA256 or gitblob(raw) != PINNED_GIT_BLOB:
        raise RuntimeError("WRONG_UPSTREAM_ORIGINAL_SOURCE")
    parsed = sexprs(raw)
    original = extract_mixed_original(parsed)
    native = native_original_relations(parsed, original)
    native.update({"now":original["now"],"next":original["next"]})
    now=original["now"]
    # The frozen parser alpha-renames source-bound SMT symbols; their names
    # are not the names in the original synth-inv parameter list. The exact
    # pinned 695-byte source plus full original semantic XOR check is authority.
    if len(now)!=5 or original["num_int"]!=5 or original["num_bool"]!=0:
        raise RuntimeError("SOURCE_INTEGER_STATE_SHAPE_DRIFT")
    parity=check_parity(original,native)
    if set(parity)!={"pre","trans","post"} or any(v!="unsat" for v in parity.values()):
        raise RuntimeError("NATIVE_VS_CUSTOM_ORIGINAL_PARITY_FAIL")
    if check_formula(native["pre"])!="sat" or check_formula(z3.Not(native["post"]))!="sat":
        raise RuntimeError("VACUOUS_SOURCE")
    c,x,y,x0,y0=now
    phi=(c+x-y-x0+y0)<=0
    positive=c>=0
    selected=z3.And(positive,phi)
    minimized=exact_minimum(path)
    if minimized["all_minimum_pairs"]!=[[0,5],[0,6]]:
        raise RuntimeError("MINIMUM_PAIR_RECEIPT_CHANGED")
    if [1,0,0,0,0] not in minimized["all_minimum_coefficients"][1]:
        raise RuntimeError("MINIMUM_TWO_ATOM_CERTIFICATE_NOT_FOUND")
    native_proof=source_proof(selected,native)
    checked=check_original_candidate(path,selected.sexpr(),expected_source_sha256=digest)
    canary={}
    for label,term,sha in (
        ("post_only",native["post"].sexpr(),digest),
        ("phi_only",phi.sexpr(),digest),
        ("nonnegative_only",positive.sexpr(),digest),
        ("true","true",digest),
        ("false","false",digest),
        ("smt_injection","(assert false)",digest),
        ("forged_sha",selected.sexpr(),"0"*64),
    ):
        res=check_original_candidate(path,term,expected_source_sha256=sha)
        canary[label]={"status":res["status"],"rejected":res["status"]!=ACCEPTED}
    # Prove a source-branch mutation is caught by the induction checker:
    # A fabricated edge from the valid zero state to c'=2,x'=-1 breaks phi.
    nxt=original["next"]
    fabricated=z3.And(*([v==0 for v in now]+[
        nxt[0]==2,nxt[1]==-1,nxt[2]==0,nxt[3]==0,nxt[4]==0]))
    bad=dict(native)
    bad["trans"]=z3.Or(native["trans"],fabricated)
    corrupted=source_proof(selected,bad)
    cvc5=checked.get("cvc5_original_three_vc") or {}
    good_independent=(set(cvc5)=={"initial","consecution","post"} and all(
        q.get("status")=="unsat" and q.get("returncode")==0 for q in cvc5.values()))
    checks={
        "exact_unchanged_original_source":True,
        "original_custom_native_semantics_parity":True,
        "exact_37_subset_two_predicate_minimum":minimized["goal_subset_checks"]==37 and
            minimized["minimum_predicates_from_this_eight_atom_set"]==2,
        "original_native_three_vc":native_proof.get("accepted") and
            set(native_proof.get("vcs",{}))=={"initial","consecution","post"} and
            all(v=="unsat" for v in native_proof["vcs"].values()),
        "strict_independent_cvc5_three_vc":checked.get("status")==ACCEPTED and good_independent,
        "all_negative_candidates_rejected":all(q["rejected"] for q in canary.values()),
        "mutation_rejected_by_induction":corrupted.get("vcs",{}).get("consecution")=="sat",
    }
    return {
        "schema":"neumann.q3.poly2.source_original_minimum_3vc_posthoc.v1",
        "source_path":SOURCE, "source_sha256":digest, "source_git_blob":PINNED_GIT_BLOB,
        "posthoc_already_opened":True, "first_three_origin_blind_gate":"FAIL_IMMUTABLE",
        "one_frozen_original_source_only":True,
        "selected_formula_smt2":selected.sexpr(),
        "minimized_candidate_count":2,
        "full_candidate_set_inductive_count":minimized["individual_inductive"],
        "subsets_checked_exact":minimized["goal_subset_checks"],
        "candidate_minimum_pairs":minimized["all_minimum_pairs"],
        "independent_native_vcs":native_proof.get("vcs"),
        "external_cvc5_vcs":cvc5,
        "mutation_native_vcs":corrupted.get("vcs"),
        "negative_controls":canary,"gates":checks,
        "scoped_posthoc_pass":all(checks.values()),
        "model_calls":0,"gpu_calls":0,"neural_learning_calls":0,
        "new_unseen_origin_count":0,
        "frozen_global_q3":"OPEN","global_q1_q7":"OPEN",
        "full_study_wall_ms":round((time.perf_counter_ns()-start)/1e6,3)
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    report=study(args.source_root/SOURCE)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("Q3_POLY2_MINIMUM_POSTHOC_SOURCE_CERTIFIED",report["scoped_posthoc_pass"])
    print("GLOBAL_Q1_Q7",report["global_q1_q7"])

if __name__=="__main__":
    main()
