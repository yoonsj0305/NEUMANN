"""Q2-E1: independent cvc5 replay of ALL 16 existing original inductive proofs.

ONE preregistered already-opened-source audit, Issue #259, before first execution.
This file does NOT implement a new structural proposer, learn, or benchmark models.
Original sources are sourced at a pinned external Git revision. The existing
frozen original source proof CLI is unchanged. cvc5 is a SECOND SMT BACKEND,
NOT a second independent SyGuS/semantic front-end or full proof assistant.
"""
from __future__ import annotations
import argparse
import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

HERE=Path(__file__).resolve().parent
R=HERE.parent
sys.path.insert(0,str(R/"q3v6-lazy-specialist-20261019"))
sys.path.insert(0,str(R/"q3v-branch-common-nullspace-20261019"))
sys.path.insert(0,str(R/"q3v5-cvc5-second-solver-20261019"))
from first_proof_gated_lazy_fallback import FIXED_EIGHT
from first_original_branch_nullspace import sample
from second_backend_first_audit import normalize_exact_unary_plus_smt2
from experiments.q3_source_prove import (
    prove_source, replay_original_source_bound, replay_exported_queries
)

SCHEMA="neumann.q2.external-cvc5-all-original-proof-replay.v1"
SOURCE_GIT="6ac90265b11431c9477dfbd33e3e3380234c0499"
BAD_OBLIGATIONS=("initial","consecution","post")
PROOF_STATUS="ORIGINAL_SOURCE_THREE_VC_CERTIFIED"
SPACER_STATUS="ORIGINAL_SOURCE_ONLY_SPACER_UNSAT"

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def checked_cvc5(script:str,expected:str):
    """Do not accept a cvc5 exit code, a word embedded in stderr, or UNKNOWN as proof."""
    start=time.perf_counter_ns()
    try:
        p=subprocess.run(["cvc5","--lang","smt2"],input=script,text=True,
            capture_output=True,timeout=15)
        lines=[x.strip() for x in p.stdout.strip().splitlines() if x.strip()]
        return {
            "expected":expected,"observed":lines,
            "returncode":p.returncode,"stderr_excerpt":p.stderr[:320],
            "pass":p.returncode==0 and lines==[expected],
            "wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
            "smt2_sha256":sha(script.encode()),"smt2_bytes":len(script)
        }
    except Exception as exc:
        return {"expected":expected,"pass":False,
            "failure":type(exc).__name__+":"+str(exc)[:180],
            "wall_ms":round((time.perf_counter_ns()-start)/1e6,3)}

def all_opened_source_paths(root:Path):
    paths=list(sample(root))+[root/path for path in FIXED_EIGHT]
    if len(paths)!=18 or len({str(p) for p in paths})!=18:
        raise RuntimeError("ORIGINAL_18_COHORT_NOT_EXACTLY_FROZEN")
    return paths

def run(root:Path):
    version=subprocess.check_output(["cvc5","--version"],text=True,timeout=7).strip()
    source_sha=[]
    rows=[]
    representative=None
    for source in all_opened_source_paths(root):
        t0=time.perf_counter_ns()
        rel=source.relative_to(root).as_posix()
        data=source.read_bytes()
        source_digest=sha(data)
        source_sha.append(source_digest)
        row={"original_path":rel,"source_sha256":source_digest,
             "status":"NOT_EVALUATED","original_3vc":{},
             "native_cvc5_results":{},"all_three_external_unsat":False}
        try:
            receipt=prove_source(source)
            row["status"]=receipt.get("status","NO_STATUS")
            row["selected_route"]=receipt.get("selected_route","UNKNOWN")
            if receipt.get("source_sha256")!=source_digest:
                raise RuntimeError("ORIGINAL_SOURCE_IDENTITY_MISMATCH")
            if receipt.get("status")==PROOF_STATUS:
                queries=receipt.get("original_bad_condition_smt2")
                if type(queries)!=dict or set(queries)!=set(BAD_OBLIGATIONS):
                    raise RuntimeError("THREE_ORIGINAL_SMT2_MISSING")
                results={}
                for key in BAD_OBLIGATIONS:
                    q=queries[key]
                    if sha(q["query"].encode())!=q["sha256"] or q["expected"]!="unsat":
                        raise RuntimeError("UNTRUSTED_QUERY_HASH_OR_STATUS")
                    normalized,rewrites=normalize_exact_unary_plus_smt2(q["query"])
                    result=checked_cvc5(normalized,"unsat")
                    result["original_sha256"]=q["sha256"]
                    result["unary_plus_syntax_only_rewrites"]=rewrites
                    results[key]=result
                row["native_cvc5_results"]=results
                row["original_3vc"]=receipt["original_three_vc"]
                row["all_three_external_unsat"]=all(
                    x["pass"] for x in results.values())
                if representative is None and receipt.get("selected_route") in (
                    "OCTAGON_HOUDINI","BRANCH_AFFINE_NULLSPACE"):
                    representative=(source,receipt)
            elif receipt.get("status")==SPACER_STATUS:
                if receipt.get("original_bad_condition_smt2") is not None:
                    raise RuntimeError("SPACER_FALSE_3VC_PROMOTION")
                row["no_inductive_certificate_provided"]=True
            else:
                row["reason"]=receipt.get("reason","NO_VALID_ORIGINAL_PROOF")
        except Exception as exc:
            row["status"]="ABSTAIN_ORIGINAL_PROOF_OR_CVC5"
            row["reason"]=type(exc).__name__+":"+str(exc)[:240]
        row["case_wall_ms"]=round((time.perf_counter_ns()-t0)/1e6,3)
        rows.append(row)

    control={}
    # True native cvc5 SAT and UNSAT are necessary but NOT sufficient for source binding.
    control["actual_sat_observation"]=checked_cvc5(
        "(set-logic QF_LIA)\n(assert true)\n(check-sat)\n","sat")
    control["forged_trivial_unsat_observation"]=checked_cvc5(
        "(set-logic QF_LIA)\n(assert false)\n(check-sat)\n","unsat")
    if representative is None:
        control["genuine_source_bound_replay"]=False
        control["legacy_three_forged_unsat_accepted"]=False
        control["forged_replay_source_bound_rejected"]=False
        control["modified_original_source_rejected"]=False
    else:
        source,real=representative
        control["representative_original_source_sha256"]=real["source_sha256"]
        control["genuine_source_bound_replay"]=bool(
            replay_original_source_bound(source,real))
        forged=copy.deepcopy(real)
        fake="(set-logic QF_LIA)\n(assert false)\n(check-sat)\n"
        for k in BAD_OBLIGATIONS:
            forged["original_bad_condition_smt2"][k]={
                "query":fake,"sha256":sha(fake.encode()),"expected":"unsat"}
        control["legacy_three_forged_unsat_accepted"]=bool(
            replay_exported_queries(forged))
        control["forged_replay_source_bound_rejected"]=not (
            replay_original_source_bound(source,forged))
        with tempfile.TemporaryDirectory() as td:
            changed=Path(td)/"modified_original.sl"
            changed.write_bytes(source.read_bytes()+b"\n;source was modified\n")
            control["modified_original_source_rejected"]=not (
                replay_original_source_bound(changed,real))

    counts=Counter(x["status"] for x in rows)
    original_vcs=[
        check
        for x in rows if x["status"]==PROOF_STATUS
        for check in x["native_cvc5_results"].values()
    ]
    externally_unsat=sum(x["pass"] for x in original_vcs)
    original_3vc_cases=sum(
        x["status"]==PROOF_STATUS and x["all_three_external_unsat"] for x in rows)
    spacer_correct=sum(
        x["status"]==SPACER_STATUS and x.get("no_inductive_certificate_provided") is True
        for x in rows)
    controls_pass=(
        control["actual_sat_observation"]["pass"] is True
        and control["forged_trivial_unsat_observation"]["pass"] is True
        and all(control.get(k) is True for k in (
           "genuine_source_bound_replay",
           "legacy_three_forged_unsat_accepted",
           "forged_replay_source_bound_rejected",
           "modified_original_source_rejected")))
    gate=(len(rows)==18 and len(set(source_sha))==18
        and counts.get(PROOF_STATUS)==16
        and counts.get(SPACER_STATUS)==2
        and original_3vc_cases==16 and externally_unsat==48
        and len(original_vcs)==48
        and spacer_correct==2 and controls_pass)
    return {
        "schema":SCHEMA,
        "pre_registered_issue":259,
        "fixed_original_git_revision":SOURCE_GIT,
        "cvc5_binary_version":version,
        "status":"SCOPED_EXTERNAL_Q2_ORIGINAL_PROOF_PASS" if gate
            else "FIRST_EXTERNAL_Q2_PROOF_FAIL_OR_UNKNOWN",
        "gate_pass":gate,
        "opened_source_original_count":len(rows),
        "unique_original_source_sha":len(set(source_sha)),
        "original_three_vc_cases":original_3vc_cases,
        "independent_external_unsat_original_bad_conditions":externally_unsat,
        "original_three_vc_queries_checked":len(original_vcs),
        "spacer_source_only_without_invariant":spacer_correct,
        "original_status_counts":dict(counts),
        "negative_and_positive_controls":control,
        "cases":rows,
        "source_language":"PINNED_ORIGINAL_LOOPINVGEN_SyGuS_LIA",
        "certification_not_independent_frontend":True,
        "learned_semantic_novelty":"NOT_EVALUATED",
        "no_fresh_unseen_generalization":True,
        "model_calls":0,"gpu_calls":0,"frontier_calls":0,
        "historical_am1_scientific_verdict":"FAIL_UNCHANGED",
        "Q2_global":"OPEN","Q1_Q7_global":"OPEN",
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    r=run(a.root)
    a.out.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    print("Q2_ALL_ORIGINAL_NATIVE_CVC5_STATUS",r["status"])
    print("Q2_ALL_ORIGINAL_NATIVE_CVC5_COUNTS",
        r["independent_external_unsat_original_bad_conditions"],
        "/",r["original_three_vc_queries_checked"],
        "original_3vc_cases",r["original_three_vc_cases"],
        "SPACER_no_invariant",r["spacer_source_only_without_invariant"])
    print("Q2_ALL_ORIGINAL_SOURCE_BOUND_CONTROLS",r["negative_and_positive_controls"])
    print("Q2_ALL_ORIGINAL_EXTERNAL_GATE",r["gate_pass"])
    print("Q2_GLOBAL",r["Q2_global"])
if __name__=="__main__":main()
