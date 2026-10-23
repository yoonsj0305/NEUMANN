"""Q3 DEV: actual cross-task trained grammar router on external-original ERBench.

IMPORTANT:
- Human supplied exact typed grammar {RATIONAL,SIN,COS,EXP,LOG,SQRT,OTHER},
  NOT genuine spontaneous operator invention.
- Train on true ORIGINAL equation-category labels from nonoverlap public sources.
- Test on untouched hash-rank original tasks #64..95; predictor sees only x/y.
- All candidate expressions submitted BEFORE independently opening target equations.
- Same-rights exhaustive classical enumerates ALL templates and rational functions.
"""
import argparse,ast,collections,hashlib,json,math,pathlib,time,warnings
import numpy as np
import sympy as sp
from erbench_original_third import allowed_formula,domain,calc,FUN,rational_fit,save,sha
X=sp.Symbol('x')
CATEGORIES=('RATIONAL','SIN','COS','EXP','LOG','SQRT','OTHER')
FN={'SIN':sp.sin,'COS':sp.cos,'EXP':sp.exp,'LOG':sp.log,'SQRT':sp.sqrt}
TRAIN_RANK_START=96
TRAIN_RANK_END=2096
SEED=1733

def features(x,y):
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float)
    if len(x)<16 or len(y)!=len(x) or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        return None
    order=np.argsort(x);x=x[order];y=y[order]
    xx=(x-np.mean(x))/max(1e-12,np.std(x))
    yy=(y-np.median(y))/max(1e-12,np.std(y))
    yy=np.clip(yy,-15,15)
    # Independent shape features; no original formula leakage.
    q=np.linspace(0,1,18)
    v=np.interp(q,np.linspace(0,1,len(x)),yy)
    dy=np.diff(yy);dd=np.diff(dy)
    g=[np.log1p(max(0.0,float(np.max(np.abs(x))))),
       np.log1p(max(0.0,float(np.max(np.abs(y))))),
       np.log1p(max(0.0,float(np.ptp(x)))),
       np.log1p(max(0.0,float(np.ptp(y)))),
       float(np.median(np.abs(dy))),float(np.median(np.abs(dd))),
       float(np.mean(dy>0)),float(np.mean(dy<0)),
       float(np.mean(np.abs(yy)>5)),float(np.mean(np.signbit(y))),
       float(np.mean(np.signbit(x))),float(np.mean(yy**2))]
    ans=np.r_[v,g]
    if not np.all(np.isfinite(ans)):return None
    return np.clip(ans,-30,30).tolist()

def formula_label(tree):
    fun=[n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
    if not fun:return 'RATIONAL'
    if len(fun)==1:
        name=fun[0]
        rem={'sin':'SIN','cos':'COS','exp':'EXP','log':'LOG','sqrt':'SQRT'}.get(name)
        if rem:return rem
    return 'OTHER'

def precompute(root,train_out):
    """Original train labels accessed ONLY here; withheld 32 identities/expression absent."""
    raw=pathlib.Path(root).read_bytes()
    assert sha(raw)=='03c0ceb53ed0348650c0a94ed5cd1e452325d2b7c7d3be68f9a458316eda33b1'
    import csv
    rows=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    eligible=[]
    for i,r in enumerate(rows):
        try:
            tree,var=allowed_formula(r['expression'])
            lo,hi,status=domain(r.get('support',''))
        except Exception:continue
        eligible.append((i,r,tree,var,lo,hi))
    eligible.sort(key=lambda e:sha((str(e[1]['collection'])+'\x1f'+str(e[1]['task_ID'])+'\x1f'+str(e[0])).encode()))
    assert len(eligible)==5717
    tasks=eligible[TRAIN_RANK_START:TRAIN_RANK_END]
    assert len(tasks)==TRAIN_RANK_END-TRAIN_RANK_START
    train=[];counts=collections.Counter()
    for i,r,tree,var,lo,hi in tasks:
        try:
            uid=sha((r['collection']+'\x1f'+r['task_ID']+'\x1f'+str(i)).encode())[:24]
            rng=np.random.default_rng(int(uid[:12],16))
            points=[]
            for x in rng.uniform(lo,hi,size=130):
                try:
                    with np.errstate(all='ignore'):y=float(calc(tree,{var:float(x)},FUN))
                    if np.isfinite(y) and abs(y)<1e9:points.append((float(x),y))
                except Exception:pass
                if len(points)>=40:break
            if len(points)<24:continue
            feat=features([p[0] for p in points],[p[1] for p in points])
            if feat is None:continue
            label=formula_label(tree)
            train.append({'features':feat,'class':label})
            counts[label]+=1
        except Exception:continue
    assert len(train)>=350
    payload={'schema':'NEUMANN_ERBENCH_TRAIN_LABELS_FROM_OTHER_AUTHOR_ORIGINALS.v1',
             'train_position_start':TRAIN_RANK_START,'train_position_end_exclusive':TRAIN_RANK_END,
             'evaluation_position_start':64,'evaluation_position_end_exclusive':96,
             'fixed_public_dataset_sha256':sha(raw),
             'no_eval_original_expressions':True,'grammar_human_fixed':list(CATEGORIES),
             'count':len(train),'counts':dict(counts),'training_observed_numeric_and_target_grammar_category_only':train}
    digest=save(train_out,payload)
    print('ERBENCH_TRAINING_SEPARATE_ORIGINALS_PREPARED',json.dumps({'n':len(train),'categories':dict(counts),'sha256':digest}),flush=True)

def candidate_fit_kind(kind,x,y):
    """Only source numbers, never original equation AST."""
    start=time.process_time()
    if kind=='RATIONAL':
        out,cpu=rational_fit(x,y)
        return (out['expr'] if out else None),cpu
    if kind=='OTHER':return None,time.process_time()-start
    bases=[]
    for z in (X,2*X,X/2,X+1,X-1):
        bases.append(FN[kind](z))
    x=np.array(x,dtype=float);y=np.array(y,dtype=float)
    for base in bases:
        try:
            fun=sp.lambdify(X,base,modules='numpy')
            with np.errstate(all='ignore'):value=np.broadcast_to(np.asarray(fun(x),dtype=float),y.shape)
            if not np.all(np.isfinite(value)) or np.std(value)<1e-10:continue
            A=np.column_stack((value,np.ones_like(value)))
            a,b=np.linalg.lstsq(A,y,rcond=1e-12)[0]
            if not (np.isfinite(a) and np.isfinite(b)):continue
            with np.errstate(all='ignore'):
                if np.max(abs((a*value+b)-y)/(1+abs(y)))>1e-8:continue
            ar=sp.Rational(float(a)).limit_denominator(1000)
            br=sp.Rational(float(b)).limit_denominator(1000)
            expression=sp.cancel(ar*base+br)
            check=sp.lambdify(X,expression,modules='numpy')
            with np.errstate(all='ignore'):
                evaluated=np.broadcast_to(np.asarray(check(x),dtype=float),y.shape)
                if not np.all(np.isfinite(evaluated)):continue
                if np.max(abs(evaluated-y)/(1+abs(y)))>1e-8:continue
            return str(expression),time.process_time()-start
        except Exception:continue
    return None,time.process_time()-start

def run_policy(row,kinds):
    x=row.get('x');y=row.get('y')
    if x is None:return {'status':'UNKNOWN_SOURCE','candidate':None,'try_sequence':[], 'cpu_s':0}
    selected=[]
    started=time.process_time()
    for kind in kinds:
        expression,cpu=candidate_fit_kind(kind,x,y)
        selected.append({'kind':kind,'candidate':expression is not None,'cpu_s':cpu})
        if expression:
            return {'status':'UNVERIFIED_PROPOSAL','candidate':expression,'candidate_kind':kind,
                    'try_sequence':selected,'cpu_s':time.process_time()-started}
    return {'status':'UNKNOWN_NO_VALID_NUMERIC_AST','candidate':None,
            'try_sequence':selected,'cpu_s':time.process_time()-started}

def train_and_predict(train_json,source_json,out):
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import StandardScaler
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        train=json.loads(pathlib.Path(train_json).read_text())
        source=json.loads(pathlib.Path(source_json).read_text())
        vals=train['training_observed_numeric_and_target_grammar_category_only']
        data=np.asarray([x['features'] for x in vals],dtype=float)
        labels=np.asarray([x['class'] for x in vals])
        assert len(vals)>=350 and len(source['source_numeric_without_equations'])==32
        ss=StandardScaler().fit(data)
        model=MLPClassifier(hidden_layer_sizes=(32,),random_state=SEED,max_iter=200,
                            early_stopping=False,learning_rate_init=0.008,alpha=0.02)
        start=time.process_time()
        model.fit(ss.transform(data),labels)
        trained_cpu=time.process_time()-start
    # Predictor has NO original test formula; only numeric source and learnt weights.
    categorical=[]
    methods={'neural_top2':[],'fixed_classical_top2':[],'classical_full_library':[]}
    inference_start=time.process_time()
    for row in source['source_numeric_without_equations']:
        feat=features(row.get('x',[]),row.get('y',[])) if 'x' in row else None
        if feat is None:
            routing=list(CATEGORIES)
            scores={c:0 for c in CATEGORIES}
        else:
            probs=model.predict_proba(ss.transform(np.asarray([feat])))[0]
            scores={name:float(prob) for name,prob in zip(model.classes_,probs)}
            routing=sorted(CATEGORIES,key=lambda c:(-scores.get(c,0),CATEGORIES.index(c)))
        categorical.append({'id':row['id'],'learned_ranking':routing,'probabilities':scores})
        methods['neural_top2'].append({'id':row['id'],**run_policy(row,routing[:2])})
        methods['fixed_classical_top2'].append({'id':row['id'],**run_policy(row,CATEGORIES[:2])})
        methods['classical_full_library'].append({'id':row['id'],**run_policy(row,CATEGORIES)})
    inference_cpu=time.process_time()-inference_start
    artifact={'schema':'NEUMANN_Q3_ERBENCH_REAL_TRAINED_ROUTE_ORIGINAL_THIRD32.v1',
        'neural_training_from_original_formula_grammar_labels_no_eval_gold':True,
        'train_src_sha256':sha(pathlib.Path(train_json).read_bytes()),
        'eval_source_numeric_sha256':sha(pathlib.Path(source_json).read_bytes()),
        'train_n':len(vals),'train_label_counts':train['counts'],
        'mlp_32hidden_architecture_human_selected':True,
        'grammar_and_operator_set_human_given':list(CATEGORIES),
        'new_operators_neurally_invented':False,
        'training_cpu_s':trained_cpu,'shared_inference_cpu_s':inference_cpu,
        'weights_hash_sha256':sha(json.dumps({
           'coefs':[q.tolist() for q in model.coefs_],
           'intercepts':[q.tolist() for q in model.intercepts_]},sort_keys=True).encode()),
        'routes':categorical,
        'methods':methods,
        'score_scope':'PRIVATE_GRADE_ORIGINAL_EXACT_EXPRESSIONS_ONLY',
        'global_Q3_Q4_Q6':'OPEN'}
    ident=save(out,artifact)
    print('Q3_ERBENCH_REAL_LEARNED_GRAMMAR_SEALED',json.dumps({
        'sha256':ident,'training':len(vals),'train_cpu_s':trained_cpu,
        'learned_proposals':sum(t['candidate'] is not None for t in methods['neural_top2']),
        'full_classical_proposals':sum(t['candidate'] is not None for t in methods['classical_full_library']),
        'full_library_per_task_mean_CPU_s':float(np.mean([t['cpu_s'] for t in methods['classical_full_library']]))},
        sort_keys=True),flush=True)

def independent_grade(truth_json,pred_json,out):
    """Source truth opened only AFTER sealed predictions. Exact mathematical equality."""
    from erbench_original_third import calc as expression,allowed_formula as parse,SYM
    info=json.loads(pathlib.Path(truth_json).read_text())
    predictions=json.loads(pathlib.Path(pred_json).read_text())
    truths=info['private_true_equations']
    assert len(truths)==32
    results={}; totals={}
    for method,rows in predictions['methods'].items():
        ix={a['id']:a for a in rows}
        counter=collections.Counter();separate=[]
        for truth in truths:
            rid=truth['id'];candidate=ix[rid]['candidate'];counter['all']+=1
            admit=False;why='UNKNOWN_ABSTAIN'
            if candidate is not None:
                try:
                    original_tree,var=parse(truth['original_expression'])
                    true=expression(original_tree,{var:X},SYM)
                    # FULL source native syntax, no numeric-only success.
                    proposed=expression(ast.parse(candidate.replace('^','**'),mode='eval'),{'x':X},SYM)
                    admit=sp.cancel(sp.together(true-proposed))==0
                    why='EXACT_ORIGINAL_EQUIVALENT' if admit else 'REJECTED_NON_EQUIVALENT'
                except Exception as e:why='UNKNOWN_SYMPY_UNSUPPORTED_'+type(e).__name__
            if admit:counter['exact']+=1
            else:counter['not_exact']+=1
            if candidate is None:counter['abstain']+=1
            elif not admit:counter['rejected']+=1
            separate.append({'id':rid,'collection':truth['collection'],'task_ID':truth['task_ID'],
                             'formula_sha256':sha(truth['original_expression'].encode()),
                             'status':why,'candidate_kind':ix[rid].get('candidate_kind')})
        results[method]=separate;totals[method]=dict(counter)
    unique=[]
    for i in range(32):
        a=results['neural_top2'][i]['status']=='EXACT_ORIGINAL_EQUIVALENT'
        b=results['classical_full_library'][i]['status']=='EXACT_ORIGINAL_EQUIVALENT'
        if a and not b:unique.append(results['neural_top2'][i]['id'])
    report={'schema':'NEUMANN_Q3_ORIGINAL_THIRD32_LEARNED_ROUTER_INDEPENDENT_AUTHOR_GRADE.v1',
       'sealed_preds_sha256':sha(pathlib.Path(pred_json).read_bytes()),
       'source_true_original_sha256':sha(pathlib.Path(truth_json).read_bytes()),
       'trained_on_disjoint_public_original_formula_labels':True,
       'no_train_original_eval_overlap':True,
       'neural_d_only_vs_strong_exhaustive_originals':unique,
       'independently_graded':totals,
       'full_original_rows':results,
       'current_grammar_human_supplied':True,
       'complete_specialist_PySR_Operon':'NOT_EXECUTED',
       'Q3_learned_new_primitive':'OPEN',
       'Q6_cross_author_transfer':'OPEN',
       'Q4_all_cost_10x':'OPEN',
       'G1_pass':False}
    name=save(out,report)
    print('Q3_ERBENCH_LEARNED_THIRD32_INDEPENDENT_ORIGINAL_GRADE',
          json.dumps({'sha256':name,'scores':totals,'neural_unique_vs_full_classical':len(unique)},sort_keys=True),flush=True)
    assert all(counts['all']==32 for counts in totals.values())
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=('prepare_train','infer','grade'),required=True)
    for key in ('csv_path','train','source','truth','pred','out'):
        p.add_argument('--'+key.replace('_','-'))
    a=p.parse_args()
    if a.mode=='prepare_train':precompute(a.csv_path,a.train)
    elif a.mode=='infer':train_and_predict(a.train,a.source,a.pred)
    else:independent_grade(a.truth,a.pred,a.out)
