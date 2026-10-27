"""Fail-closed *research* gate for one original SMT-LIB 2 script.

A SAT/UNSAT is only a verdict for the `check-sat` query, never a proof
that requested interpolants, models, unsat cores, or formal proof objects
were generated/checked. This scanner is deliberately conservative and does
NOT parse arbitrary SMT-LIB or verify an SMT theorem independently.
"""
import re
GOAL_PAT=re.compile(r'\((get-interpolants?|get-proof|get-model|get-unsat-core)\b',re.I)
CHECK_PAT=re.compile(r'\(check-sat(?:-assuming)?\b',re.I)

def check_authority(original_smt:str, solver_stdout:str, exit_code:int):
    if exit_code!=0:
        return {'status':'HOLD_EXECUTOR_ERROR','verified_full_original':False}
    if GOAL_PAT.search(original_smt):
        return {'status':'HOLD_ADDITIONAL_GOAL_NOT_VERIFIED','verified_full_original':False}
    lines=[s.strip() for s in solver_stdout.splitlines() if s.strip()]
    if not lines or any(s.lower()=='unsupported' or s.lower().startswith(('error:','(error')) for s in lines):
        return {'status':'HOLD_SOLVER_ERROR','verified_full_original':False}
    answers=[s for s in lines if s in {'sat','unsat','unknown'}]
    num_checks=len(CHECK_PAT.findall(original_smt))
    if num_checks==0 or len(answers)!=num_checks or len(answers)!=len(lines):
        return {'status':'HOLD_INCOMPLETE_OR_UNRECOGNIZED_OUTPUT','verified_full_original':False}
    if 'unknown' in answers:
        return {'status':'HOLD_SOLVER_UNKNOWN','verified_full_original':False}
    return {'status':'SMT_VERDICT_ONLY','solver_answers':answers,
            'verified_full_original':False,'independent_proof_object':False}
