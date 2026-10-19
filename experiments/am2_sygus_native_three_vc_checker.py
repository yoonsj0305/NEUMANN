"""AM2 one REAL source-bound original invariant checker, not neural proof research.

Source: exact public SyGuS .sl original, never answer keys.
Candidate: caller-proposed standalone SMT-LIB Bool FORMULA only, not a JSON PASS.
Checker: native rederived original Pre/Trans/Post inductive 3VC and standalone cvc5.
First test prereg: GitHub Issue #267. Historical Q3 real source evidence unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import z3

from experiments.q3_source_prove import (
    MAX_INPUT_BYTES, _obligations, check_formula, check_parity,
    extract_mixed_original, native_original_relations, prove_source,
    replay_original_source_bound, sexprs, source_proof, EXPECTED,
)

SCHEMA="neumann.am2.sygus-original-candidate-checker.v1"
FROZEN_CASES=(
    "comp/2018/Inv_Track/cggmp2005_true-unreach-call_true-termination.sl",
    "comp/2018/Inv_Track/bkley.sl",
)
MAX_FORMULA_BYTES=4096

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def _fail(reason,original_sha=None,candidate_sha=None):
    return {"schema":SCHEMA,"status":"ABSTAIN_ORIGINAL_NOT_CERTIFIED",
            "reason":reason,"original_sha256":original_sha,
            "candidate_sha256":candidate_sha,"native_original_three_vc":None,
            "cvc5_original_three_vc":None,"original_source_bound":False,
            "independent_model_calls":0,"gpu_calls":0,
            "global_Q1_Q7":"OPEN"}

def _single_formula(candidate:str,source_vars):
    """Reject SMT-LIB command injection; only one pure Boolean assertion term."""
    if type(candidate) is not str:
        raise ValueError("NOT_PLAIN_TEXT_FORMULA")
    raw=candidate.encode()
    if not raw or len(raw)>MAX_FORMULA_BYTES:
        raise ValueError("FORMULA_SIZE_CAP")
    if "\x00" in candidate or ";" in candidate:
        raise ValueError("SMTLIB_COMMAND_COMMENT_UNSUPPORTED")
    if any(t in candidate.lower() for t in (
        "(assert","(declare-","(define-","(set-","(check-",
        "(push","(pop","(exit","(get-")):
        raise ValueError("MODEL_COMMAND_INJECTION_REJECTED")
    decls={v.decl().name():v for v in source_vars}
    parsed=z3.parse_smt2_string("(assert "+candidate+")",decls=decls)
    if len(parsed)!=1 or not z3.is_bool(parsed[0]):
        raise ValueError("NOT_ONE_BOOL_PREDICATE")
    return parsed[0]

def _independent_cvc5(script:str):
    try:
        p=subprocess.run(["cvc5","--lang=smt2","--tlimit-per=3000","-"],
             input=script,text=True,capture_output=True,
             timeout=8,check=False)
        tokens=[x.strip() for x in p.stdout.splitlines() if x.strip()]
        return {"status":tokens[-1] if tokens else "EMPTY",
            "returncode":p.returncode,"stderr_excerpt":p.stderr[:120]}
    except Exception as e:
        return {"status":"NO_INDEPENDENT_BACKEND",
                "reason":type(e).__name__+":"+str(e)[:110]}

def check_original_candidate(source_path:Path,candidate:str,
        *,expected_source_sha256:str):
    """True only after ACTUAL original inductiveness, independent solver and SHA.

    This function does not generate a good invariant; the candidate comes
    from an external proposer and is not allowed to read original checker
    secrets. All original source semantics are reconstructed here.
    """
    source_path=Path(source_path)
    if source_path.suffix!=".sl" or source_path.is_symlink() or not source_path.is_file():
        return _fail("NOT_TRUSTED_ORIGINAL_SOURCE_FILE")
    raw=source_path.read_bytes()
    digest=sha(raw)
    if len(raw)>MAX_INPUT_BYTES:
        return _fail("SOURCE_SIZE_CAP",digest)
    if type(expected_source_sha256) is not str or digest!=expected_source_sha256:
        return _fail("ORIGINAL_SOURCE_IDENTITY_MISMATCH",digest)
    candidate_digest=sha(candidate.encode()) if type(candidate) is str else None
    try:
        parsed=sexprs(raw)
        original=extract_mixed_original(parsed)
        native=native_original_relations(parsed,original)
        native.update({"now":original["now"],"next":original["next"]})
        parity=check_parity(original,native)
        if len(parity)!=3 or any(v!="unsat" for v in parity.values()):
            raise ValueError("ORIGINAL_NATIVE_CUSTOM_PARSER_MISMATCH")
        if check_formula(native["pre"])!="sat":
            raise ValueError("ORIGINAL_INITIAL_STATES_NOT_SAT")
        if check_formula(z3.Not(native["post"]))!="sat":
            raise ValueError("ORIGINAL_SAFETY_GOAL_VACUOUS")
        invariant=_single_formula(candidate,original["now"])
        proof=source_proof(invariant,native)
        if not proof["accepted"] or proof["vcs"]!=EXPECTED:
            return {**_fail("FAILED_ACTUAL_ORIGINAL_INDUCTION",digest,candidate_digest),
               "native_original_three_vc":proof["vcs"],
               "status":"REJECTED_ORIGINAL_BAD_CONDITION"}
        outcomes={}
        for key,condition in _obligations(invariant,original,native).items():
            solver=z3.Solver()
            solver.set(timeout=2500)
            solver.add(condition)
            if solver.check()!=z3.unsat:
                return _fail("UNABLE_TO_EXPORT_EXACT_ORIGINAL_VC",digest,candidate_digest)
            cross=_independent_cvc5(solver.to_smt2())
            outcomes[key]=cross
        if set(outcomes)!={"initial","consecution","post"} or any(
                x["status"]!="unsat" or x["returncode"]!=0 for x in outcomes.values()):
            return {**_fail("INDEPENDENT_CVC5_NOT_VERIFIED",digest,candidate_digest),
                "cvc5_original_three_vc":outcomes}
        return {"schema":SCHEMA,"status":"CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5",
            "original_sha256":digest,"candidate_sha256":candidate_digest,
            "native_original_three_vc":proof["vcs"],
            "cvc5_original_three_vc":outcomes,
            "original_source_bound":True,
            "independent_model_calls":0,"gpu_calls":0,
            "global_Q1_Q7":"OPEN"}
    except Exception as e:
        return _fail(type(e).__name__+":"+str(e)[:160],digest,candidate_digest)

def first_two_real_source_gate(root:Path):
    rows=[]
    for rel in FROZEN_CASES:
        source=root/rel
        if source.is_symlink() or not source.is_file():
            raise RuntimeError("FROZEN_SOURCE_FILE_MISSING:"+rel)
        fixed_sha=sha(source.read_bytes())
        original_positive=prove_source(source)
        if original_positive["status"]!="ORIGINAL_SOURCE_THREE_VC_CERTIFIED":
            raise RuntimeError("PINNED_CLASSICAL_POSITIVE_NOT_AVAILABLE:"+rel)
        if not replay_original_source_bound(source,original_positive):
            raise RuntimeError("POSITIVE_ORIGINAL_SOURCE_BOUND_REPLAY_FAILED:"+rel)
        positive=check_original_candidate(source,original_positive["invariant_sexpr"],
            expected_source_sha256=fixed_sha)
        bad_true=check_original_candidate(source,"true",
            expected_source_sha256=fixed_sha)
        bad_false=check_original_candidate(source,"false",
            expected_source_sha256=fixed_sha)
        bad_identity=check_original_candidate(source,original_positive["invariant_sexpr"],
            expected_source_sha256="0"*64)
        bad_command=check_original_candidate(source,"(assert false)",
            expected_source_sha256=fixed_sha)
        row={"public_original_path":rel,"original_sha256":fixed_sha,
             "original_classical_positive_route":original_positive["selected_route"],
             "positive":positive,
             "negative_true":bad_true,
             "negative_false":bad_false,
             "negative_wrong_source_sha":bad_identity,
             "negative_command_injection":bad_command,
             "uses_already_opened_source":True}
        rows.append(row)
        print("SOURCE_BOUND_ORIGINAL_CHECKER",rel,
              positive["status"],bad_true["status"],bad_false["status"],
              bad_identity["status"],bad_command["status"])
    checks={
        "both_actual_public_sources_available":len(rows)==2,
        "both_real_positive_candidates_certified":all(
            r["positive"]["status"]=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5" for r in rows),
        "six_independent_original_bad_queries_unsat":all(
            len(r["positive"]["cvc5_original_three_vc"])==3 and
            all(q["status"]=="unsat" and q["returncode"]==0
                for q in r["positive"]["cvc5_original_three_vc"].values()) for r in rows),
        "four_intentionally_wrong_true_or_false_candidates_rejected":all(
            r[name]["status"]=="REJECTED_ORIGINAL_BAD_CONDITION" for r in rows
            for name in ("negative_true","negative_false")),
        "two_source_sha_tamper_controls_rejected":all(
            "IDENTITY_MISMATCH" in r["negative_wrong_source_sha"].get("reason","") for r in rows),
        "two_smt_command_injections_rejected":all(
            r["negative_command_injection"]["status"]!="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5" for r in rows),
    }
    return {"schema":"neumann.am2.first-real-sygus-original-checker.v1",
        "preregistered_issue":267,
        "real_original_verifier_executable_coverage":"SYGUS_3VC_ONLY",
        "scope":"TWO_ALREADY_OPENED_PUBLISHED_ORIGINALS_ONE_VERIFIER_MODALITY",
        "frozen_original_count":2,"cases":rows,"checks":checks,
        "first_scoped_checker_pass":all(checks.values()),
        "new_unseen_originals":0,"original_source_families_admitted_for_ex1":0,
        "am2_24_original_cohort_admitted":False,
        "learned_new_operator_proven":False,
        "model_calls":0,"gpu_calls":0,"paid_api_calls":0,
        "sealed_sources_opened":False,"global_Q1_Q7":"OPEN"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    report=first_two_real_source_gate(a.source_root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("FIRST_SYGUS_REAL_CHECKER_GATES",json.dumps(report["checks"],sort_keys=True))
    print("FIRST_SYGUS_REAL_CHECKER_SCOPED_PASS",report["first_scoped_checker_pass"])
if __name__=="__main__":main()
