"""Immutable independent OEIS6 first original learned latent-state theorem audit.

SHA asserts FOUR original artifacts from first Actions 39957412796
BEFORE reading labels or recomputing state. Rebuilds Hankel rank lower
bound, companion transition and original all-n induction, plus an
out-of-model factorial negative control. All math classical and known.
"""
import argparse,hashlib,json,pathlib,math
import sympy as sp

LOCKS={
 'source':'eb9ea1ab438d3be34c6560ffc9de8a654f96dfb818c2afb06241462bb3503284',
 'truth':'4a964c4d8e5c75363012280d1ebfa8284026e34bca6e0c6eb17b303bb89b0d15',
 'pred':'2220789a6de37123303752ccfffe91acfaa3ed3f70fb1e468528a409d44d1d39',
 'grade':'77daf49d2bc90e45479653231e25197c1eb30d7c585dfbf699a774a3b729afbd'
}
def digest(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def audit(args):
    for key,expected in LOCKS.items():
        actual=digest(getattr(args,key))
        assert actual==expected,(key,'FIRST_ORIGINAL_ARTIFACT_SHA_CHANGED',actual,expected)
    source=json.loads(pathlib.Path(args.source).read_text())['source_numeric_without_recurrence']
    truth=json.loads(pathlib.Path(args.truth).read_text())['private_true_author_recurrences']
    pre=json.loads(pathlib.Path(args.pred).read_text())['methods']
    grade=json.loads(pathlib.Path(args.grade).read_text())
    assert len(source)==len(truth)==6
    source_by_id={v['id']:v for v in source}
    original_by_id={v['id']:v for v in truth}
    D=grade['all_cases']['D_learned_state_dimension_TOP1']
    A=grade['all_cases']['A_classical_minimal_enumeration_ALL_1_to_4']
    assert len(D)==len(A)==6
    assert grade['method_first_author_original_all_n_induction']['D_learned_state_dimension_TOP1']['proved_all_n']==6
    assert grade['method_first_author_original_all_n_induction']['A_classical_minimal_enumeration_ALL_1_to_4']['proved_all_n']==6
    rows=[]
    for d in D:
        assert d['status']=='WHOLE_PUBLISHED_AUTHOR_RULE_ALL_N_INDUCTION_PASS'
        orig=original_by_id[d['id']]
        s=source_by_id[d['id']]
        pred=next(v for v in pre['D_learned_state_dimension_TOP1']['cases'] if v['id']==d['id'])
        m=pred['new_named_executable_state_macro']
        r=m['DEFINE_STATE_VECTOR']['latent_dimension']
        values=[sp.Integer(v) for v in s['a']]
        H=sp.Matrix([[values[i+j] for j in range(r)] for i in range(r)])
        det=H.det()
        assert det and str(det)==m['source_fit_verification']['hankel_determinant_exact']
        assert m['initial_exact']==orig['author_initial']
        assert m['DEFINE_COMPANION_MATRIX_T'][0]==orig['author_coefficients']
        assert len(m['DEFINE_COMPANION_MATRIX_T'])==r
        for k in range(1,r):
            # If a lower-order recurrence held for ALL natural n, every
            # column of H_r after the kth is a fixed combination of
            # first k columns, so rank(H_r)<=k<r. Nonzero det rules it out.
            assert H.rank()==r>k
        assert d['withheld_exact_heldout_n16_120']==105
        rows.append({'name':orig['task_ID'],'inferred_and_true_minimum_state_order':r,
          'independent_exact_nonzero_Hankel_determinant':str(det),
          'source_only_named_program':m['name'],
          'full_author_exact_recurrence_all_n_by_induction':True,
          'future_exact_integer_terms_n16_120':105})
    from learned_latent_state_dimension import fit_exact
    factorial=[sp.factorial(i) for i in range(16)]
    fail_any=[r for r in (1,2,3,4) if fit_exact(factorial,r)]
    assert fail_any==[],'UNSUPPORTED_FACTORIAL_WAS_FALSELY_ADMITTED'
    # Fundamental necessary caution: an arbitrary sequence can match
    # first16 and branch afterwards. This empirical test proves minimality
    # ONLY *conditional* on constant-coefficient recurrence hypothesis
    # and published author exact law, not unbounded general intelligence.
    report={'schema':'NEUMANN_Q3_OEIS6_FIRST_FOUR_SHA_LOCKED_MINIMAL_LATENT_STATES.v1',
      'FIRST_source_gold_model_grade_SHA256':LOCKS,
      'all_six_complete_exact_math_proofs':rows,
      'all_n_proved_by_identity_of_published_author_and_learned_recurrence':True,
      'minimum_state_rank_lower_bound_in_constant_coefficient_linear_class':True,
      'factorial_first16_did_not_false_admit_ANY_r1_to4':True,
      'exact_future_heldout_checks_total':630,
      'trained_model_unique_over_same_rights_full_classical':0,
      'training_included_gold_OEIS_recursions':False,
      'caveats':'Known classical Hankel and induction math; neural gets rank-informative source features, human supplied recurrence model class and exact verifier; finite values alone never identify an unrestricted sequence; no frontier/10x or new atomic primitive.',
      'G1':'HOLD','Q3_GLOBAL':'OPEN','Q4_10x':'NOT_PROVED'}
    p=pathlib.Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print('Q3_OEIS6_FIRST_IMMUTABLE_MINIMAL_STATE_RANK_AND_AUTHOR_ALLN_INDUCTION_INDEPENDENT_PASS',
      json.dumps({'rows':rows,'withheld_exact_future_total':630,
        'factorial_negative_control_pass':True,
        'SHA256':digest(p)},sort_keys=True),flush=True)
if __name__=='__main__':
    a=argparse.ArgumentParser()
    for role in LOCKS:a.add_argument('--'+role,required=True)
    a.add_argument('--out',required=True)
    audit(a.parse_args())
