"""Original CellARC structural reconstruction from source demonstrations only."""
import collections,functools,json

@functools.lru_cache(maxsize=32)
def debruijn(k,n):
    a=[0]*(k*n)
    out=[]
    def visit(t,p):
        if t>n:
            if n%p==0:out.extend(a[1:p+1])
        else:
            a[t]=a[t-p]
            visit(t+1,p)
            for j in range(a[t-p]+1,k):
                a[t]=j
                visit(t+1,t)
    visit(1,1)
    assert len(out)==k**n
    return tuple(out)

def occurs_on_cycle(fragment,cycle):
    n=len(cycle)
    return any(all(x==cycle[(pos+j)%n] for j,x in enumerate(fragment)) for pos in range(n))

def source_models(task):
    allvals=[x for d in task['train'] for x in d['input']]+list(task['query'])
    if not allvals:return []
    observed_k=max(allvals)+1
    matches=[]
    for k in range(max(2,observed_k),7):
        for W in (3,5,7):
            if k**W>512:continue
            R=(W-1)//2
            possible=[(r,R//r) for r in (1,2,3) if R%r==0 and R//r<=5]
            if not possible:continue
            cycle=debruijn(k,W)
            if all(occurs_on_cycle(pair['input'],cycle) for pair in task['train']):
                matches.append({'k':k,'W':W,'effective_radius':R,'possible_radius_steps':possible})
    return matches

def features(window,kind):
    m=len(window)//2
    if kind=='full':return window
    if kind=='sum':return (sum(window),)
    if kind=='center_and_outer':return (window[m],sum(window)-window[m])
    if kind=='center_and_histogram':return (window[m],tuple(sorted(collections.Counter(window[:m]+window[m+1:]).items())))
    raise ValueError(kind)

def fit_model(task,R,kind):
    table={}
    for d in task['train']:
        x,y=d['input'],d['output']
        for i in range(R,len(x)-R):
            key=features(tuple(x[i-R:i+R+1]),kind)
            if key in table and table[key]!=y[i]:return None
            table[key]=y[i]
    return table if table else None

def infer(task):
    options=source_models(task)
    if len(options)!=1:
        return {'status':'NO_UNIQUE_GENERATOR_STRUCTURE','number_of_models':len(options),'prediction':None}
    info=options[0]
    q=task['query'];R=info['effective_radius'];n=len(q)
    if n<2*R+1:
        return {'status':'QUERY_TOO_SHORT','structural_model':info,'prediction':None}
    windows=[tuple(q[(i+j)%n] for j in range(-R,R+1)) for i in range(n)]
    preds={}
    for kind in ('full','sum','center_and_outer','center_and_histogram'):
        table=fit_model(task,R,kind)
        if table is not None:
            keys=[features(w,kind) for w in windows]
            if all(k in table for k in keys):preds[kind]=[table[k] for k in keys]
    uniq={tuple(p) for p in preds.values()}
    if len(uniq)!=1:
        return {'status':'NO_UNIQUE_PREDICTION','structural_model':info,'compatible_model_families':list(preds),'prediction':None}
    return {'status':'SOURCE_INDUCED_CYCLE_PREDICTION','structural_model':info,
            'compatible_model_families':list(preds),'prediction':list(next(iter(uniq)))}
