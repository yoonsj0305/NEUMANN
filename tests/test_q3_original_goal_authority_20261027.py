import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'/'q3'/'discovery_policy'))
from original_goal_authority import check_authority as gate

def test_sat_only_is_scoped_solver_verdict():
 s=gate('(assert true) (check-sat)', 'sat\n',0)
 assert s['status']=='SMT_VERDICT_ONLY' and not s['verified_full_original']

def test_interpolant_unsat_not_full_original():
 s=gate('(assert false) (check-sat) (get-interpolants IP_0 IP_1)','unsat\nunsupported\n',0)
 assert s['status']=='HOLD_ADDITIONAL_GOAL_NOT_VERIFIED'

def test_unsupported_or_error_is_hold():
 assert gate('(check-sat)','unsat\nunsupported\n',0)['status']=='HOLD_SOLVER_ERROR'
 assert gate('(check-sat)','Error: unsat\n',0)['status']=='HOLD_SOLVER_ERROR'

def test_unknown_and_missing_proof_are_hold():
 assert gate('(check-sat)','unknown',0)['status']=='HOLD_SOLVER_UNKNOWN'
 assert gate('(assert false)','',0)['status']!='SMT_VERDICT_ONLY'
