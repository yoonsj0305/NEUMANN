"""NEUMANN Q3/G1 scientific acceptance guard, source-first equal-budget protocol.

This verifier enforces consistency of signed first-run RESULT FIELDS only.
It is NOT a cryptographic independently trusted grader: caller must actually
verify input bytes vs listed SHA and gold source separation before publication.
Positive synthetic logic tests never prove model performance.
"""
import argparse
import hashlib
import json
from pathlib import Path

def report(receipt):
    failures=[]
    proof_fields=('registration_sha256','source_sha256','pregrade_prediction_sha256',
       'independent_grade_sha256','shared_primitive_authority_sha256',
       'classical_precommit_sha256')
    for field in proof_fields:
        value=receipt.get(field,'')
        if not (isinstance(value,str) and len(value)==64 and
                all(ch in '0123456789abcdef' for ch in value)):
            failures.append('MISSING_SHA:'+field)
    for k in ('prediction_frozen_before_grader_truth','source_gold_physically_isolated',
              'same_primitive_semantics_and_verifier_rights',
              'independent_author_family_holdout'):
        if receipt.get(k) is not True:failures.append('FIRST_SOURCE_CONTRACT_FAIL:'+k)
    if receipt.get('strong_baseline_kind')!='specialist_GP_or_CEGIS':
        failures.append('BASELINE_NOT_MATCHED_STRONG_SPECIALIST')
    if receipt.get('complete_classical_grammar_enumerator'):
        failures.append('IMPOSSIBLE_G1_EXCLUSIVE_SUPERSET_COMPARISON')
    rows=receipt.get('original_cases',[])
    if len(rows)<8:failures.append('ORIGINAL_COHORT_TOO_SMALL')
    ids=[r.get('id') for r in rows]
    if not all(ids) or len(set(ids))!=len(ids):
        failures.append('INVALID_ORIGINAL_IDENTITIES')
    if set(ids)&set(receipt.get('training_or_dev_ids',[])):
        failures.append('CONTAMINATED_PRIOR_ORIGINAL_COHORT')
    if len({r.get('author_family') for r in rows})<2:
        failures.append('SINGLE_AUTHOR_FAMILY')
    nn_cost=receipt.get('learner_train_and_replay_CPU_s')
    classical_cost=receipt.get('classical_train_CPU_s')
    if not isinstance(nn_cost,(int,float)) or nn_cost<0:
        failures.append('MISSING_TRAIN_COST');nn_cost=0.
    if not isinstance(classical_cost,(int,float)) or classical_cost<0:
        failures.append('MISSING_CLASSICAL_COST');classical_cost=0.
    exclusive=[]
    families=set()
    exact_nn=exact_classic=0
    for row in rows:
        ident=row.get('id')
        d,a=row.get('learner_author_full_function_exact'),row.get('classical_author_full_function_exact')
        if not isinstance(d,bool) or not isinstance(a,bool):
            failures.append('UNVERIFIED_WHOLE_AUTHOR_FUNCTION:'+str(ident));continue
        exact_nn+=d;exact_classic+=a
        if d and not a:
            if not (row.get('learned_typed_AST') and
                    row.get('independent_AST_semantics_audit') is True and
                    row.get('actual_neural_edit_tape_provenance') is True):
                failures.append('UNPROVED_NEW_MODEL_CREATED_EXPRESSION:'+str(ident))
            exclusive.append(ident);families.add(row.get('author_family'))
        for who in ('learner','classical'):
            cpu=row.get(who+'_test_source_and_verifier_CPU_s')
            calls=row.get(who+'_verifier_calls')
            if not isinstance(cpu,(int,float)) or cpu<0:
                failures.append('MISSING_TEST_CPU:'+who+':'+str(ident));cpu=0
            if not isinstance(calls,int) or calls<0:
                failures.append('MISSING_TEST_ORACLE_CALLS:'+who+':'+str(ident))
            if who=='learner':nn_cost+=cpu
            else:classical_cost+=cpu
    if len(exclusive)<2:failures.append('FEWER_THAN_TWO_LEARNER_EXCLUSIVE')
    if len(families)<2:failures.append('LEARNER_NOT_TRANSFERRING_BETWEEN_AUTHORS')
    budget=receipt.get('equal_precommitted_total_CPU_budget_s')
    if not isinstance(budget,(int,float)) or budget<=0:
        failures.append('NOT_SAME_FINITE_TOTAL_CPU_BUDGET')
    elif nn_cost>budget or classical_cost>budget:
        failures.append('OVER_PRECOMMITTED_TOTAL_BUDGET')
    if nn_cost>classical_cost:
        failures.append('NOT_MORE_COMPUTE_EFFICIENT_THAN_STRONG_CLASSICAL')
    return {'verdict':'PASS' if not failures else 'OPEN','failed_conditions':failures,
       'learned_exact_authored_originals':int(exact_nn),
       'strong_classical_exact_authored_originals':int(exact_classic),
       'learned_exclusive_whole_authored_originals':exclusive,
       'genuine_extra_author_families':sorted(families),
       'measured_neural_train_test_CPU_s':nn_cost,
       'measured_classical_train_test_CPU_s':classical_cost,
       'provenance_warning':'Boolean/sha fields must be checked against actual remote artifact bytes and run order independently. Synthetic fixture PASS is not evidence of a new NEUMANN model.'}

def selftest():
    h=hashlib.sha256(b'precommitted').hexdigest()
    base={k:h for k in ('registration_sha256','source_sha256',
        'pregrade_prediction_sha256','independent_grade_sha256',
        'shared_primitive_authority_sha256','classical_precommit_sha256')}
    base.update(prediction_frozen_before_grader_truth=True,
      source_gold_physically_isolated=True,
      same_primitive_semantics_and_verifier_rights=True,
      independent_author_family_holdout=True,
      strong_baseline_kind='specialist_GP_or_CEGIS',
      complete_classical_grammar_enumerator=False,
      learner_train_and_replay_CPU_s=0.1,classical_train_CPU_s=0.1,
      equal_precommitted_total_CPU_budget_s=3.0,
      original_cases=[{'id':'fixture_'+str(i),
       'author_family':'AUTHOR_A' if i<4 else 'AUTHOR_B',
       'learner_author_full_function_exact':i in (0,4),
       'classical_author_full_function_exact':False,
       'learned_typed_AST':'variable_length_REWRITE_AST' if i in (0,4) else None,
       'independent_AST_semantics_audit':i in (0,4),
       'actual_neural_edit_tape_provenance':i in (0,4),
       'learner_test_source_and_verifier_CPU_s':0.1,
       'classical_test_source_and_verifier_CPU_s':0.2,
       'learner_verifier_calls':1,'classical_verifier_calls':3} for i in range(8)])
    assert report(base)['verdict']=='PASS'
    import copy
    for mutant in (
        lambda d:d.update(complete_classical_grammar_enumerator=True),
        lambda d:d.update(equal_precommitted_total_CPU_budget_s=.01),
        lambda d:d['original_cases'][0].update(id='dev'),
        lambda d:d['original_cases'][0].update(actual_neural_edit_tape_provenance=False),
        lambda d:d['original_cases'][4].update(learner_author_full_function_exact=False),
        lambda d:d.update(source_gold_physically_isolated=False)):
        m=copy.deepcopy(base);mutant(m)
        if m['original_cases'][0]['id']=='dev':m['training_or_dev_ids']=['dev']
        assert report(m)['verdict']=='OPEN'
    print('G1_EQUAL_BUDGET_GATE_1_SYNTHETIC_LOGIC_POSITIVE_6_NEGATIVES_PASS_NOT_MODEL_PERFORMANCE')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--receipt');parser.add_argument('--out')
    parser.add_argument('--selftest',action='store_true')
    p=parser.parse_args()
    if p.selftest:selftest()
    if p.receipt:
        z=report(json.loads(Path(p.receipt).read_text()))
        if p.out:Path(p.out).write_text(json.dumps(z,indent=2))
        print(json.dumps(z,ensure_ascii=False,indent=2))
    if not p.selftest and not p.receipt:parser.error('Pass --selftest or --receipt')
