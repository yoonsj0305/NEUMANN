"""Postgrade audit only, no new blind claim or solution leakage. Preserves SHA-sealed first ERBench original32 predictions and compares FORMAL representability in the fixed bounded 1D rational function language."""
import argparse,collections,hashlib,json,pathlib
import sympy as sp
from erbench_original_first import allowed_formula,calc,SYM
S={
  'truth':'4b51cd3cc41727892bb4dcd854906425c0f9e35049fc1a3100395450488c08ef',
  'pred':'8c606012c29dacbcdf6f8a65131726bb1ca20856a8d10e2b57d062b36eb5430e',
  'grade':'05a8709366bdeb4e531bc9c863d6ffe1c4e4ceb176c3d072a3f85458fe735850'
}
def digest(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def examine(exp):
    x=sp.Symbol('x')
    try:
        tree,name=allowed_formula(exp)
        source=calc(tree,{name:x},SYM)
        reduced=sp.cancel(sp.together(source))
        if not reduced.is_rational_function(x):
            return {'category':'NOT_RATIONAL_IN_SOURCE_SYMPY_NORMAL_FORM',
                    'rational_fixed_grammar_coverage':False}
        top,bottom=sp.fraction(reduced)
        npoly=sp.Poly(top,x);dpoly=sp.Poly(bottom,x)
        degN=int(npoly.degree());degD=int(dpoly.degree())
        if min(degN,degD)<0:
            return {'category':'UNSUPPORTED_ZERO_OR_DEGENERATE'}
        # Rational numerical regressor restricts all coefficients to Q.
        rational=all(c.is_Rational for c in npoly.all_coeffs()+dpoly.all_coeffs())
        # Scalar polynomial factor cancellation is part of sp.cancel above.
        if not rational:
            category='RATIONAL_IN_X_BUT_NONRATIONAL_SCALAR_COEFFICIENT'
        elif degN<=4 and degD<=2:
            category='ORACLE_INSIDE_FINITE_RATIONAL_GRAMMAR'
        else:
            category='RATIONAL_OUTSIDE_DEGREE_CAP'
        return {'category':category,'degree_N':degN,'degree_D':degD,
                'source_coefficients_all_rational':bool(rational),
                'rational_fixed_grammar_coverage':category=='ORACLE_INSIDE_FINITE_RATIONAL_GRAMMAR'}
    except Exception as e:
        return {'category':'UNKNOWN_SYMPY_PARSE_OR_PROOF',
                'error':type(e).__name__+':'+str(e)[:80],
                'rational_fixed_grammar_coverage':None}
def main():
    p=argparse.ArgumentParser()
    for key in ('truth','pred','grade','out'):p.add_argument('--'+key,required=True)
    args=p.parse_args()
    for role in ('truth','pred','grade'):
        actual=digest(getattr(args,role))
        assert actual==S[role],(role,actual,S[role])
    truth=json.loads(pathlib.Path(args.truth).read_text())['private_true_equations']
    preds=json.loads(pathlib.Path(args.pred).read_text())['predictions']
    grades=json.loads(pathlib.Path(args.grade).read_text())['all_rows']
    assert len(truth)==len(preds)==len(grades)==32
    pp={r['id']:r for r in preds}
    gg={r['id']:r for r in grades}
    seen=set();cases=[];totals=collections.Counter()
    for t in truth:
        uid=t['id']
        assert uid not in seen and uid in pp and uid in gg;seen.add(uid)
        cls=examine(t['original_expression'])
        candidate=pp[uid]
        original_grade=gg[uid]
        totals[cls['category']]+=1
        totals['total']+=1
        totals['numerical_candidate']+=int(candidate['status']=='UNVERIFIED_PROPOSAL')
        totals['first_exact']+=int(original_grade['status']=='EXACT_ORIGINAL_FORMULA_EQUIVALENCE')
        # Avoid making assertions about first-run candidate results beyond recorded grader.
        cases.append({'id':uid,'collection':t['collection'],'task_ID':t['task_ID'],
                      'original_formula_sha256':hashlib.sha256(t['original_expression'].encode()).hexdigest(),
                      'original_expression_classification':cls,
                      'first_source_prediction_status':candidate['status'],
                      'first_independent_grade_status':original_grade['status']})
    assert totals['total']==32 and totals['first_exact']==0
    result={'schema':'NEUMANN_ERBENCH_POSTGRADE_ORIGINAL32_GRAMMAR_CEILING_AUDIT.v1',
        'historical_first_unchanged_SHA256':S,'source_unblinded_for_audit':True,
        'source_original_dataset':'ERBench EquationDiscovery public train10000',
        'baseline_grammar':'Q-coefficient 1D rational P degree<=4 / Q degree<=2',
        'scope':'POSTGRADE_GRAMMAR_CLASSIFICATION_ONLY_NOT_NEW_PROSPECTIVE_G1',
        'important_limit':'a symbolic form in a recognized category is not a proof that no other semantics or solver technique could recover the answer; stronger symbolic regression baselines not run',
        'categories':dict(totals),'cases':cases,'G0':'HOLD_STRONG_SPECIALIST',
        'G1_LEARNED_NEW_OPERATOR':'NOT_ADMITTED',
        'Q3_GLOBAL':'OPEN','Q4_TOTAL10X':'OPEN'}
    dest=pathlib.Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print('ERBENCH_FIRST32_ORIGINAL_POSTGRADE_GRAMMAR_AUDIT',
          json.dumps({'counts':dict(totals),
                      'report_sha256':digest(dest)},sort_keys=True),flush=True)
if __name__=='__main__':main()
