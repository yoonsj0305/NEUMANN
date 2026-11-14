"""NEUMANN Q3: learned required LATENT STATE DIMENSION, create typed state machine.

Learns graph-state dimension r in [1,4] from independently generated numeric
sequences. Training labels are produced by the exact SOURCE-ONLY recurrence
verifier, never an author's recurrence rule. At test, MLP selects r TOP1,
then constructs from input values only:

 DEFINE_STATE_VECTOR Z_n=(a(n),a(n-1),...,a(n-r+1))
 DEFINE_COMPANION_MATRIX T_r
 STEP Z_(n+1)=T_r Z_n
 EMIT y(n)=Z_n[0]

Full symbolic output/functional induction proof is INDEPENDENT grader-only,
using first published OEIS recurrence after all first source proposals frozen.
The human predefined linear-recurrence algorithm and maximum r=4; this is
NOT a learned novel atomic mathematical primitive nor a frontier claim.
"""
import argparse,hashlib,json,pathlib,time,warnings,collections
import numpy as np
import sympy as sp
from sklearn.neural_network import MLPClassifier

SEED=20261023
ORDERS=(1,2,3,4)
TRAIN_PER_CLASS=72

def hash_bytes(raw):return hashlib.sha256(raw).hexdigest()
def write(path,value):
    p=pathlib.Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    return hash_bytes(p.read_bytes())
def ints(series):
    if len(series)!=16:return None
    try:
        v=[sp.Integer(x) for x in series]
        if not all(i.is_Integer for i in v):return None
        return v
    except Exception:return None

def fit_exact(v,r):
    """Source-only exact rational minimum-order linear recurrence certificate.

    Every candidate MUST fit all prefix source n<16. Higher-order padded
    fits with rank deficient design are UNKNOWN, not claimed unique.
    """
    assert len(v)==16 and 1<=r<=4
    A=sp.Matrix([[v[n-j-1] for j in range(r)] for n in range(r,len(v))])
    Y=sp.Matrix(v[r:])
    if A.rank()!=r:return None
    if A.row_join(Y).rank()!=r:return None
    try:
        weights,free=A.gauss_jordan_solve(Y)
    except ValueError:return None
    if free.rows!=0:return None
    ws=[sp.cancel(x) for x in weights]
    if not all(w.is_Rational for w in ws):return None
    if any(w.q>100 for w in ws):return None
    if any(sp.cancel(v[n]-sum(ws[j]*v[n-j-1] for j in range(r)))!=0 for n in range(r,16)):
        return None
    H=sp.Matrix([[v[i+j] for j in range(r)] for i in range(r)])
    det=H.det()
    if det==0:return None
    return {'r':r,'coefficients':[str(w) for w in ws],
        'initial_exact':[str(x) for x in v[:r]],
        'hankel_determinant_exact':str(det),
        'first16_recurrence_exact':True,
        'exact_source_prefix_SHA256':hash_bytes(json.dumps([str(x) for x in v]).encode())}

def generator(coeff,init,count=16):
    r=len(coeff);a=[sp.Integer(x) for x in init]
    while len(a)<count:
        a.append(sum(coeff[j]*a[-1-j] for j in range(r)))
    return a

def features(v):
    """Source-only Hankel geometry, NO original gold recurrence labels."""
    f=np.asarray([float(x) for x in v],float)
    f=f/max(np.max(np.abs(f)),1.)
    h=np.array([[f[i+j] for j in range(7)] for i in range(7)],float)
    singular=np.linalg.svd(h,compute_uv=False)
    s=np.clip(singular/max(singular[0],1e-18),1e-14,1)
    return np.r_[np.log10(s),f[:8],np.diff(f[:7])]

def train_self_reward():
    rng=np.random.default_rng(SEED)
    samples=[];counts=collections.Counter();checks=0
    start=time.process_time()
    for r in ORDERS:
        admitted=0;tries=0
        while admitted<TRAIN_PER_CLASS:
            tries+=1;assert tries<5000,('FAILED_TO_GET_SOURCE_EXACT_CLASS',r)
            coeff=[sp.Integer(int(rng.choice([-3,-2,-1,1,2,3]))) for _ in range(r)]
            if coeff[-1]==0:continue
            if rng.random()<.7:
                init=[0]*(r-1)+[1]
            else:
                init=[int(i) for i in rng.integers(-3,4,size=r)]
                if not any(init):continue
            seq=generator(coeff,init,16)
            if max(abs(v) for v in seq)>10**15:continue
            results=[]
            for order in ORDERS:
                checks+=1
                q=fit_exact(seq,order)
                if q:results.append(q)
            if not results:continue
            best=min(results,key=lambda x:x['r'])
            if best['r']!=r:continue
            samples.append({'first16_source':[str(x) for x in seq],
                 'structure_label_from_source_only_exact_verifier':best['r'],
                 'source_verifier_witness_SHA256':hash_bytes(json.dumps(best,sort_keys=True).encode())})
            counts[best['r']]+=1;admitted+=1
    verifierCPU=time.process_time()-start
    X=np.array([features([sp.Integer(x) for x in s['first16_source']]) for s in samples])
    Y=np.array([s['structure_label_from_source_only_exact_verifier'] for s in samples])
    assert len(samples)==288 and all(counts[k]==72 for k in ORDERS)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        model=MLPClassifier(hidden_layer_sizes=(32,16),max_iter=650,
             random_state=SEED,learning_rate_init=.004,alpha=.012)
        t=time.process_time();model.fit(X,Y);fitCPU=time.process_time()-t
    training_fit=float(np.mean(model.predict(X)==Y))
    assert training_fit>=.80,('SELF_REWARD_LEARNING_FAILED',training_fit)
    report={'training_source_simulated_without_OEIS_truth':True,
       'training_valid_source_sequences':len(samples),'classes':dict(counts),
       'exact_source_verifier_labels_not_teacher_graph_gold':True,
       'training_source_exact_fit_oracle_calls':checks,
       'source_first16_value_dataset_SHA256':hash_bytes(json.dumps(samples,sort_keys=True).encode()),
       'MLP_weights_SHA256':hash_bytes(json.dumps([c.tolist() for c in model.coefs_],sort_keys=True).encode()),
       'train_source_oracle_CPU_s':verifierCPU,'train_neural_MLP_CPU_s':fitCPU,
       'neural_on_training_source_accuracy':training_fit,
       'human_supplied_actions_and_operator_meanings':['DEFINE_STATE_VECTOR','DEFINE_COMPANION_MATRIX','STEP_LINEAR','EMIT'],
       'human_supplied_max_state_dimension':4,
       'new_semantically_atomic_primitive':'NOT_LEARNED'}
    return model,report

def build_program(src,r):
    v=ints(src['a'])
    if v is None:return None
    witness=fit_exact(v,r)
    if not witness:return None
    w=[sp.Rational(x) for x in witness['coefficients']]
    T=[[str(w[j]) for j in range(r)]]
    for j in range(1,r):
        T.append(['1' if q==j-1 else '0' for q in range(r)])
    assert len(T)==r and all(len(row)==r for row in T)
    macro={'node':'DEFINE_MACRO','name':'M_'+hash_bytes(json.dumps(witness,sort_keys=True).encode())[:12],
           'parameter':'n','output':'state_component_0',
           'DEFINE_STATE_VECTOR':{'latent_dimension':r,'components':['a(n-'+str(i)+')' for i in range(r)]},
           'DEFINE_COMPANION_MATRIX_T':T,
           'DEFINE_RECURSIVE_STEP':'S_(n+1)=T*S_n',
           'initial_exact':witness['initial_exact'],
           'source_fit_verification':witness,
           'derived_coefficients_from_only_observed_sequence':True}
    return macro

def infer(trainpath,sourcepath,predpath):
    model,learning=train_self_reward()
    raw=pathlib.Path(sourcepath).read_bytes();data=json.loads(raw)
    rows=data['source_numeric_without_recurrence']
    assert len(rows)==6 and all('author_coefficients' not in r for r in rows)
    rng=np.random.default_rng(3001)
    arms={}
    mode_names=['D_learned_state_dimension_TOP1','C_untrained_random_TOP1',
      'C_fixed_dimension_2','C_fixed_dimension_4','A_classical_minimal_enumeration_ALL_1_to_4']
    for mode in mode_names:
        begin=time.process_time();cases=[];checks=0
        for row in rows:
            v=ints(row['a']);assert v is not None
            if mode=='D_learned_state_dimension_TOP1':
                chosen=[int(model.predict([features(v)])[0])]
            elif mode=='C_untrained_random_TOP1':chosen=[int(rng.choice(ORDERS))]
            elif mode=='C_fixed_dimension_2':chosen=[2]
            elif mode=='C_fixed_dimension_4':chosen=[4]
            else:chosen=list(ORDERS)
            seen=[];chosen_macro=None
            for order in chosen:
                checks+=1
                candidate=build_program(row,order)
                seen.append({'tested_state_dimension':order,'state_source_verified':candidate is not None})
                if candidate is not None:
                    chosen_macro=candidate
                    if mode.startswith('A_classical'):break
            cases.append({'id':row['id'],'task_ID':row['task_ID'],
             'source_only_tested_structure_states':seen,
             'new_named_executable_state_macro':chosen_macro,
             'status':'SOURCE_EXACT_RECURRENCE_FOUND' if chosen_macro else 'UNKNOWN'})
        arms[mode]={'cases':cases,'source_oracle_calls':checks,
                    'source_model_CPU_s':time.process_time()-begin,
                    'source_valid_macro_count':sum(bool(c['new_named_executable_state_macro']) for c in cases)}
    result={'schema':'NEUMANN_Q3_FIRST_OEIS6_SOURCE_LEARNED_HIDDEN_STATE_DIMENSION.v1',
       'training':learning,'test_source_without_author_rule_SHA256':hash_bytes(raw),
       'model_decides_memory_state_vector_dimension':True,
       'typed_new_state_companion_matrix_created_from_source':True,
       'every_published_author_rule_physically_withheld_during_infer':True,
       'first_originals':6,'methods':arms,'G1':'HOLD','Q3_GLOBAL':'OPEN'}
    digest=write(predpath,result)
    print('Q3_FIRST_SIX_OEIS_EXTERNAL_ORIGINALS_LEARNED_LATENT_STATE_AND_COMPANION_GRAPH_SOURCE_ONLY',json.dumps({
       'SHA256':digest,'trained_numeric_tasks':learning['training_valid_source_sequences'],
       'learning_training_accuracy':learning['neural_on_training_source_accuracy'],
       'training_CPU':learning['train_source_oracle_CPU_s']+learning['train_neural_MLP_CPU_s'],
       'cases':{k:{'source_valid':v['source_valid_macro_count'],
                    'oracle_calls':v['source_oracle_calls'],
                    'process_cpu_s':v['source_model_CPU_s'],
                    'inferred_dimensions':{c['task_ID']:
                    (c['new_named_executable_state_macro'] or {}).get('DEFINE_STATE_VECTOR',{}).get('latent_dimension')
                     for c in v['cases']}} for k,v in arms.items()}},sort_keys=True),flush=True)

def reconstruct_from_macro(macro,n_max):
    r=macro['DEFINE_STATE_VECTOR']['latent_dimension']
    y=[sp.Rational(v) for v in macro['initial_exact']]
    T=sp.Matrix([[sp.Rational(x) for x in row] for row in macro['DEFINE_COMPANION_MATRIX_T']])
    assert T.shape==(r,r)
    for n in range(r,n_max+1):
        y.append((T*sp.Matrix([y[n-j-1] for j in range(r)]))[0])
    return y

def grade(truthpath,predpath,outpath):
    raw=pathlib.Path(predpath).read_bytes();dat=json.loads(raw)
    private=pathlib.Path(truthpath).read_bytes();gold=json.loads(private)['private_true_author_recurrences']
    original={r['id']:r for r in gold}
    assert len(gold)==6
    methods={};cases={}
    for mode,p in dat['methods'].items():
        done=[];exact=0;nonminimal=0
        for case in p['cases']:
            target=original[case['id']];hyp=case['new_named_executable_state_macro']
            success=False;holdout=0;minimal=False;reason=None
            if hyp is not None:
                r=hyp['DEFINE_STATE_VECTOR']['latent_dimension']
                ct=[sp.Rational(x) for x in hyp['DEFINE_COMPANION_MATRIX_T'][0]]
                gt=[sp.Rational(x) for x in target['author_coefficients']]
                seeds=[sp.Rational(x) for x in target['author_initial']]
                seed_hyp=[sp.Rational(x) for x in hyp['initial_exact']]
                v=reconstruct_from_macro(hyp,120)
                holdout=sum(int(v[int(row['n'])]==sp.Integer(row['a'])) for row in target['exact_heldout_n16_120'])
                det=sp.Rational(hyp['source_fit_verification']['hankel_determinant_exact'])
                minimal=(det!=0 and r==len(gt))
                success=(r==len(gt) and ct==gt and seed_hyp==seeds and holdout==105 and minimal)
                if not success:reason='NOT_AUTHOR_FULL_RECURRENCE_OR_HOLDOUT'
            else:reason='NO_SOURCE_CERTIFIED_STATE_PROGRAM'
            exact+=int(success)
            nonminimal+=int(not minimal)
            done.append({'id':case['id'],'original':target['task_ID'],
                 'status':'WHOLE_PUBLISHED_AUTHOR_RULE_ALL_N_INDUCTION_PASS' if success else 'UNKNOWN',
                 'first_source_hidden_state_dimension':
                     hyp['DEFINE_STATE_VECTOR']['latent_dimension'] if hyp else None,
                 'author_full_recurrence_matched_exactly':success,
                 'nonzero_Hankel_rank_lower_bound':minimal,
                 'same_as_original_for_ALL_nonnegative_integers_by_induction':success,
                 'withheld_exact_heldout_n16_120':holdout,
                 'underlying_first_source_generated_program':hyp if success else None,
                 'failure_reason':reason})
        methods[mode]={'total':len(done),'proved_all_n':exact,'not_proved':len(done)-exact}
        cases[mode]=done
    solved={k:{c['id'] for c in rows if c['status']=='WHOLE_PUBLISHED_AUTHOR_RULE_ALL_N_INDUCTION_PASS'} for k,rows in cases.items()}
    learner=solved['D_learned_state_dimension_TOP1']
    grade={'schema':'NEUMANN_Q3_FIRST_EXTERNAL_OEIS6_PUBLISHED_ALL_N_STATE_PROGRAM_GRADE.v1',
      'first_source_only_pregrade_sha256':hash_bytes(raw),
      'private_author_original_recurrences_sha256':hash_bytes(private),
      'method_first_author_original_all_n_induction':methods,
      'all_cases':cases,
      'learner_only_over_classical_full_same_rights':sorted(learner-solved['A_classical_minimal_enumeration_ALL_1_to_4']),
      'learner_only_over_fixed_r2':sorted(learner-solved['C_fixed_dimension_2']),
      'learner_only_over_random':sorted(learner-solved['C_untrained_random_TOP1']),
      'genuine_first_source_discovered_state_dimension_but_human_gave_matrix_rule':'TRUE',
      'linear_recurrence_model_class_human_limited_to_order4':True,
      'novel_mathematics_theorem':'NONE',
      'G1':'HOLD','Q3_GLOBAL':'OPEN','Q4_ALL_IN10X':'NOT_PROVED','Q7_FRONTIER':'NOT_TESTED'}
    digest=write(outpath,grade)
    print('Q3_FIRST_OEIS6_INDEPENDENT_AUTHOR_ALL_N_MINIMAL_STATE_PROOFS',json.dumps({
      'SHA256':digest,'methods':methods,'learned_only_over_classical_full':len(grade['learner_only_over_classical_full_same_rights']),
      'first_neural_exact_OEIS':[c['original'] for c in cases['D_learned_state_dimension_TOP1']
         if c['status']=='WHOLE_PUBLISHED_AUTHOR_RULE_ALL_N_INDUCTION_PASS']},sort_keys=True),flush=True)
    assert all(v['total']==6 for v in methods.values())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=('infer','grade'),required=True)
    for k in ('train','source','truth','pred','out'):p.add_argument('--'+k)
    a=p.parse_args()
    if a.mode=='infer':infer(a.train,a.source,a.pred)
    else:grade(a.truth,a.pred,a.out)
