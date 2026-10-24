"""Immutable-original-run truth and representability audit, after grading ONLY.

No sixth32 rerun, no new first-blind performance or tuned model evaluation.
All five first-run artifacts must match their GitHub Actions SHA receipts.
"""
import ast,argparse,collections,hashlib,json,pathlib
import sympy as s
from erbench_original_sixth import allowed_formula,calc,SYM
X=s.Symbol('x')
LOCKS={
"train":"c773efe1e31bee25fae5587f86c2d447b96888e3daf36ff73f071116ee4d5fd2",
"source":"06177e1df48a8d74e46dbc6f443302198c457f293acc0b80a4822144660cd743",
"truth":"5acfdeb8d2c75194635331640c896c5b6c6d853c189e32444c6a3811631cb6fd",
"pred":"0c547b2de0b9a3e453e8942dd8ee7c72b6709ec05b826d52010ad1a364f53db9",
"grade":"e96c50ee751eec11735b382e210a6077efb6afd405198e04f3472734f535e33c"}
def checksum(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def audit(a):
    for k in LOCKS:assert checksum(getattr(a,k))==LOCKS[k],(k,"ORIGINAL_RECEIPT_CHANGED")
    original=json.loads(pathlib.Path(a.truth).read_text())['private_true_equations']
    pred=json.loads(pathlib.Path(a.pred).read_text());grading=json.loads(pathlib.Path(a.grade).read_text())
    assert len(original)==32
    assert all(q['total']==32 for q in grading['scores'].values())
    bymethod={method:{r['id']:r for r in rows} for method,rows in grading['cases'].items()}
    counts=collections.Counter();rows=[]
    for true in original:
        ident=true["id"]
        try:
            node,var=allowed_formula(true["original_expression"])
            expr=s.cancel(s.together(calc(node,{var:X},SYM)))
            if not expr.is_rational_function(X):cls="CERTIFIED_NONRATIONAL_OUTSIDE_ARITHMETIC_DSL"
            else:
                num,den=s.fraction(expr)
                try:
                    p=s.Poly(num,X);q=s.Poly(den,X)
                    degree=(int(p.degree()),int(q.degree()))
                    cls="RATIONAL_UNDERLYING_SOURCE"
                except Exception:cls="UNKNOWN_RATIONAL_POLYNOMIAL_DEGREE"
        except Exception as e:cls="UNKNOWN_SYMPY_NORMAL_FORM_"+type(e).__name__
        counts[cls]+=1
        got={method:bymethod[method][ident]["status"] for method in bymethod}
        rows.append({'id':ident,'collection':true['collection'],'task_ID':true['task_ID'],
           'author_formula_sha256':hashlib.sha256(true['original_expression'].encode()).hexdigest(),
           'first_native_original_grade':got,'symbolic_category':cls})
    # empirical first-run same task identifiers: all three scores exact=1
    assert counts['RATIONAL_UNDERLYING_SOURCE']>=1
    assert grading['scores']['online_neural_graph_edits']['exact']==1
    assert grading['scores']['same256_random_nolearn']['exact']==1
    assert grading['scores']['complete2048_classical']['exact']==1
    stats=pred['test']
    all_candidates=stats['complete2048_classical']['first_predictions']
    neural_candidates=stats['online_neural_graph_edits']['first_predictions']
    full={c['id']:{v['lambda_expression'] for v in c['proposals']} for c in all_candidates}
    uncontained=[]
    for row in neural_candidates:
        if any(v['lambda_expression'] not in full[row['id']] for v in row['proposals']):
            uncontained.append(row['id'])
    # First sealed cohort each has <=25 proposed so no truncation
    assert not uncontained,("FIRST_SOURCE_PROGRAM_HAS_NEURAL_OUTSIDE_CLASSICAL",uncontained)
    result={'schema':'NEUMANN_Q3_ERBENCH_SIXTH32_FIRST_POSTGRADE_REPRESENTABILITY_CEILING.v1',
       'immutable_original_receipt_SHA256':LOCKS,
       'original_public_external_equations_not_blind_private':True,
       'total_originals':32,'categories':dict(counts),
       'all_original_rows':rows,
       'empirical_first_source_neural_composed_candidates_all_contained_in_full_2048_classical':True,
       'mathematical_reason':'Neural and classical enumerate the same 2048 complete AST edit sequences and use the same numeric source proof/rational repair function; accuracy-exclusive D-only solutions against error-free exhaustive A cannot occur if A preserves every accepted program. A can still take more or less CPU.',
       'first_source_candidate_counts':{method:{
           'attempts':v['program_evaluation_calls'],
           'permethod_CPU_s':v['cpu_s'],
           'source_candidates':v['source_graph_proposals']
        } for method,v in stats.items()},
        'learned_model_training_details':pred['self_reward_model'],
        'first_original_full_truth_grading':grading['scores'],
        'no_first_blind_re_evaluation':True,
        'true_new_semantic_atomic_primitive_invented':'NOT_PROVED',
        'source_cross_family_learner_advantage':'NONE',
        'G1':'HOLD'}
    dst=pathlib.Path(a.out);dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print("Q3_SIXTH32_FIRST_POSTGRADE_GRAMMAR_AND_COST_AUDIT",json.dumps({
        'counts':dict(counts),'train_successes':pred['self_reward_model']['positive_own_source_reward'],
        'learned_train_reward_CPU_s':pred['self_reward_model']['training_reward_and_candidate_CPU_s'],
        'learned_neural_fit_CPU_s':pred['self_reward_model']['fitted_neural_CPU_s'],
        'original_method_CPU':{k:v['cpu_s'] for k,v in stats.items()},
        'sealed_report_SHA256':checksum(dst)},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in LOCKS:p.add_argument('--'+k,required=True)
    p.add_argument('--out',required=True)
    audit(p.parse_args())
