"""G0: first genuine external ERBench Equation Recovery benchmark admission screen.
Source-only numerical samples physically separate from original expression truth.
All 32 fixed SHA-ID ranked 1-D eligible tasks retained. No neural claim, no G1.
"""
import argparse,ast,collections,csv,hashlib,json,operator,pathlib,re,time
import numpy as np
import sympy as sp
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Pow:operator.pow}
FUN={'sin':np.sin,'cos':np.cos,'tan':np.tan,'exp':np.exp,'log':np.log,'sqrt':np.sqrt,'abs':np.abs,'Abs':np.abs,'asin':np.arcsin,'acos':np.arccos,'atan':np.arctan,'sinh':np.sinh,'cosh':np.cosh,'tanh':np.tanh}
SYM={k:getattr(sp,{'abs':'Abs','atan':'atan','asin':'asin','acos':'acos'}.get(k,k)) for k in FUN}
def sha(x):return hashlib.sha256(x).hexdigest()
def save(path,data):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n')
    return sha(path.read_bytes())
def calc(n,scope,func):
    if isinstance(n,ast.Expression):return calc(n.body,scope,func)
    if isinstance(n,ast.Constant) and type(n.value) in (int,float):return n.value
    if isinstance(n,ast.Name):
        if n.id in scope:return scope[n.id]
        if n.id=='pi':return sp.pi if func is SYM else np.pi
        if n.id=='E':return sp.E if func is SYM else np.e
        raise ValueError('NAME_NOT_ALLOWED')
    if isinstance(n,ast.BinOp) and type(n.op) in OPS:
        return OPS[type(n.op)](calc(n.left,scope,func),calc(n.right,scope,func))
    if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -calc(n.operand,scope,func)
    if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.UAdd):return calc(n.operand,scope,func)
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in func and len(n.args)==1 and not n.keywords:
        return func[n.func.id](calc(n.args[0],scope,func))
    raise ValueError('DISALLOWED_EXPRESSION_NODE')
def allowed_formula(s):
    tree=ast.parse(s.replace('^','**'),mode='eval')
    names=sorted({n.id for n in ast.walk(tree) if isinstance(n,ast.Name) and n.id not in set(FUN)|{'pi','E'}})
    if len(names)!=1:raise ValueError('NOT_ONE_DIMENSION')
    return tree,names[0]
def domain(s):
    matches=re.findall(r'[\(\[]\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*[,;]\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*[\)\]]',str(s))
    if not matches:return -2.,2.,'FALLBACK_NOT_OFFICIAL_DOMAIN'
    low,high=map(float,matches[0])
    if not (np.isfinite(low) and np.isfinite(high) and 1e-8<high-low<1e7):raise ValueError('BAD_DOMAIN')
    return low,high,'SOURCE_DOMAIN_PARSED'
def prepare(src,source_out,truth_out,revision):
    raw=pathlib.Path(src).read_bytes();table=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    assert len(table)>=1000
    assert set(('collection','task_ID','expression','support')).issubset(table[0])
    possible=[];not_eligible=collections.Counter()
    for i,r in enumerate(table):
        try:
            tree,var=allowed_formula(r['expression'])
            lo,hi,status=domain(r.get('support',''))
            possible.append((i,r,tree,var,lo,hi,status))
        except Exception as e:not_eligible[type(e).__name__+':'+str(e)[:35]]+=1
    possible.sort(key=lambda x:sha((str(x[1]['collection'])+'\x1f'+str(x[1]['task_ID'])+'\x1f'+str(x[0])).encode()))
    cohort=possible[2256:2288]
    print('PRE_CONTENT_SAMPLE_FROZEN_IDS',json.dumps({'revision':revision,'csv_sha256':sha(raw),
          'all_originals':len(table),'one_dim_eligible':len(possible),
          'ordered_selected_ids':[x[1]['collection']+':'+x[1]['task_ID'] for x in cohort]}),flush=True)
    numeric=[];truth=[]
    for i,r,tree,var,lo,hi,domain_status in cohort:
        uid=sha((r['collection']+'\x1f'+r['task_ID']+'\x1f'+str(i)).encode())[:24]
        rng=np.random.default_rng(int(uid[:12],16))
        pts=[]
        for x in rng.uniform(lo,hi,size=400):
            try:
                with np.errstate(all='ignore'):yy=float(calc(tree,{var:float(x)},FUN))
                if np.isfinite(yy) and abs(yy)<1e9:pts.append([float(x),yy])
            except Exception:pass
            if len(pts)>=48:break
        if len(pts)==48:
            numeric.append({'id':uid,'x':[t[0] for t in pts],'y':[t[1] for t in pts],
                            'collection':r['collection'],'task_ID':r['task_ID'],'domain_status':domain_status})
        else:
            numeric.append({'id':uid,'status':'UNKNOWN_TOO_FEW_FINITE_SOURCE_POINTS',
                            'collection':r['collection'],'task_ID':r['task_ID']})
        truth.append({'id':uid,'collection':r['collection'],'task_ID':r['task_ID'],
                      'original_expression':r['expression'],'source_var':var,
                      'source_index':i,'original_support':r.get('support','')})
    ssha=save(source_out,{'schema':'NEUMANN_ERBENCH_1D_NINTH_ORIGINAL_SOURCE.v1',
          'revision':revision,'csv_sha256':sha(raw),'original_total':len(table),
          'eligible_1d':len(possible),'all_selected':len(cohort),'selection':'ninth32 indices 32:64 by sha256 of (collection,task_ID,row_index) among one-dimensional parseable expressions, no method outcomes',
          'source_numeric_without_equations':numeric})
    tsha=save(truth_out,{'original_csv_sha256':sha(raw),'private_true_equations':truth})
    print('PHYSICAL_TRUTH_SOURCE_ISOLATION',json.dumps({'n':len(numeric),'source_sha256':ssha,'truth_sha256':tsha}),flush=True)
def rational_fit(xs,ys):
    x=np.asarray(xs);y=np.asarray(ys);scale=max(1.,float(np.quantile(abs(x),.8)));z=x/scale
    start=time.process_time();best=None
    for n in range(5):
        for m in range(3):
            A=np.column_stack([z**i for i in range(n+1)]+[-y*z**i for i in range(1,m+1)])
            try:c=np.linalg.lstsq(A,y,rcond=1e-11)[0]
            except Exception:continue
            if not np.all(np.isfinite(c)) or np.max(abs(c))>1e8:continue
            nu=sum(c[i]*z**i for i in range(n+1))
            de=np.ones_like(z)+sum(c[n+i]*z**i for i in range(1,m+1))
            if np.min(abs(de))<1e-8:continue
            with np.errstate(all='ignore'):pred=nu/de
            if not np.all(np.isfinite(pred)):continue
            err=float(np.max(abs(pred-y)/(1+abs(y))))
            if err>=1e-7:continue
            # Rationalization is prior to source truth; may fail exact symbolic test.
            # CRITICAL SOURCE-ONLY FIX: move coefficients BACK to physical x, THEN rationalize.
            # z=x/scale => a_i(x)=a_i(z)/scale^i, b_j(x)=b_j(z)/scale^j.
            # The older code rationalized a_i(z), potentially destroying exact Q coefficients.
            X=sp.Symbol('x')
            ratN=[sp.Rational(float(c[j]/(scale**j))).limit_denominator(1000) for j in range(n+1)]
            ratD=[sp.Rational(float(c[n+j]/(scale**j))).limit_denominator(1000) for j in range(1,m+1)]
            num=sum(ratN[j]*X**j for j in range(n+1))
            den=1+sum(ratD[j-1]*X**j for j in range(1,m+1))
            restored=sp.cancel(num/den)
            try:
                fn=sp.lambdify(X,restored,modules='numpy')
                with np.errstate(all='ignore'):
                    recovered=np.broadcast_to(np.asarray(fn(x),dtype=float),y.shape)
                    restored_err=float(np.max(abs(recovered-y)/(1+abs(y))))
                if not np.isfinite(restored_err) or restored_err>1e-8:continue
            except Exception:continue
            candidate={'expr':str(restored),'p_degree':n,'q_degree':m,
                       'normalized_train_residual':err,'physical_rationalized_residual':restored_err}
            rank=(n+m,m,err)
            if best is None or rank<best[0]:best=(rank,candidate)
    return (best[1] if best else None),time.process_time()-start
def infer(source,out):
    inp=json.loads(pathlib.Path(source).read_text());pred=[]
    for r in inp['source_numeric_without_equations']:
        if 'x' not in r:pred.append({'id':r['id'],'status':'UNKNOWN_SOURCE','candidate':None});continue
        answer,spent=rational_fit(r['x'],r['y'])
        pred.append({'id':r['id'],'status':'UNVERIFIED_PROPOSAL' if answer else 'UNKNOWN_NO_RATIONAL_POLYNOMIAL_FIT',
                     'candidate':answer,'source_classical_cpu_s':spent})
    sealed={'schema':'NEUMANN_ERBENCH_NINTH_CLASSICAL_PREDICTION.v1',
            'source_only_sha256':sha(pathlib.Path(source).read_bytes()),'predictions':pred,
            'no_neural_learning':True,'specialist_pysr_operon_not_executed':True,'G1':'HOLD'}
    print('ERBENCH_SEALED_CLASSICAL_SOURCE_SHA256',save(out,sealed),flush=True)
def grade(truth,pred,out):
    t=json.loads(pathlib.Path(truth).read_text());p=json.loads(pathlib.Path(pred).read_text())
    pp={z['id']:z for z in p['predictions']};counts=collections.Counter();rows=[]
    for original in t['private_true_equations']:
        one=pp[original['id']];counts['total']+=1
        row={'id':original['id'],'collection':original['collection'],'task_ID':original['task_ID'],
             'original_formula_sha256':sha(original['original_expression'].encode()),'status':'UNKNOWN'}
        if one['status']=='UNVERIFIED_PROPOSAL':
            try:
                a,var=allowed_formula(original['original_expression']);X=sp.Symbol('x')
                true=calc(a,{var:X},SYM)
                guessed=calc(ast.parse(one['candidate']['expr'],mode='eval'),{'x':X},SYM)
                if sp.cancel(sp.together(true-guessed))==0:
                    row['status']='EXACT_ORIGINAL_FORMULA_EQUIVALENCE';counts['exact']+=1
                else:
                    row['status']='UNKNOWN_REJECTED_NON_EQUIVALENT';counts['rejected_non_equivalent']+=1
            except Exception as e:
                row['status']='UNKNOWN_GRADE_UNSUPPORTED';counts['unsupported']+=1
                row['error']=type(e).__name__+':'+str(e)[:70]
        else:counts['abstained']+=1
        rows.append(row)
    result={'schema':'NEUMANN_ERBENCH_NINTH_ORIGINAL_GRADE.v1',
            'prediction_sha256':sha(pathlib.Path(pred).read_bytes()),
            'source_csv_sha256':t['original_csv_sha256'],
            'counts':dict(counts),'all_rows':rows,
            'G0':'NO_ADMISSION_UNTIL_STRONG_SPECIALIST_SAME_BUDGET_COMPARISON',
            'trained_new_primitive':'NOT_TESTED','G1':'HOLD','Q3':'OPEN','Q4_10x':'OPEN'}
    print('ERBENCH_ORIGINAL_FIRST_G0',json.dumps({'counts':dict(counts),'evidence_sha256':save(out,result)},sort_keys=True),flush=True)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--mode',choices=['prepare','infer','grade'],required=True)
    for k in ('csv_path','source','truth','out','revision'):a.add_argument('--'+k.replace('_','-'))
    z=a.parse_args()
    if z.mode=='prepare':prepare(z.csv_path,z.source,z.truth,z.revision)
    elif z.mode=='infer':infer(z.source,z.out)
    else:grade(z.truth,z.source,z.out)
