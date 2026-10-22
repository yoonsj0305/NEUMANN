"""Real source-only restoration of missing boundary contexts from a canonical cycle.

Unlike masking valid source edge observations, given a hypothesized original
canonical B(k,W) cycle and its EXACT observed substrings, a global position
reconstructs each source observation's true full effective neighborhood.

This is source-based algorithmic generation matching using publicly documented
de Bruijn prior. No test targets, hidden true metadata, or neural training.
A false structural prior can still pass; independent original scoring required.
"""
import collections
from debruijn_structural_model import debruijn,source_models,infer

KINDS=('full','sum','center_outer','center_hist')
def signature(w,kind):
    if kind=='full':return w
    if kind=='sum':return (sum(w),)
    m=len(w)//2
    if kind=='center_outer':return (w[m],sum(w)-w[m])
    if kind=='center_hist':
        return (w[m],tuple(sorted(collections.Counter(w[:m]+w[m+1:]).items())))
    raise ValueError(kind)

def offsets_on_canonical(fragment,cycle):
    n=len(cycle)
    return [i for i in range(n) if all(x==cycle[(i+j)%n] for j,x in enumerate(fragment))]

def candidate(task,info):
    k,W,R=(info['k'],info['W'],info['effective_radius'])
    values=[v for p in task['train'] for v in p['output']]
    if not values or max(values)>=k:
        return {'status':'REJECT_SOURCE_OBSERVED_STATE_OUTSIDE_GENERATOR'}
    cycle=debruijn(k,W);N=len(cycle);samples=[]
    for p in task['train']:
        x,y=p['input'],p['output']
        if len(x)!=len(y) or len(x)<W:
            return {'status':'REJECT_SOURCE_CONTEXT_SHORT'}
        matches=offsets_on_canonical(x,cycle)
        if len(matches)!=1:
            return {'status':'REJECT_UNIQUE_GLOBAL_ALIGNMENT','matches':len(matches)}
        pos=matches[0]
        for j,target in enumerate(y):
            complete=tuple(cycle[(pos+j+t)%N] for t in range(-R,R+1))
            samples.append((complete,target))
    models={}
    q=task['query'];L=len(q)
    if L<2*R+1:
        return {'status':'REJECT_QUERY_TOO_SHORT'}
    windows=[tuple(q[(i+t)%L] for t in range(-R,R+1)) for i in range(L)]
    for kind in KINDS:
        table={};valid=True
        for nb,truth in samples:
            key=signature(nb,kind)
            if key in table and table[key]!=truth:
                valid=False;break
            table[key]=truth
        if not valid:continue
        keys=[signature(nb,kind) for nb in windows]
        if all(key in table for key in keys):
            models[kind]=[table[key] for key in keys]
    if not models:
        return {'status':'NO_SOURCE_COVERED_COMPLETE_PREDICTION',
                'full_boundary_observations':len(samples)}
    distinct={tuple(y) for y in models.values()}
    if len(distinct)!=1:
        return {'status':'SOURCE_MODEL_DISAGREEMENT',
                'models':list(models),'different_query_outputs':len(distinct)}
    return {'status':'ALIGNED_FULL_CONTEXT_CONSENSUS','prediction':list(next(iter(distinct))),
            'models':list(models),'full_boundary_observations':len(samples)}

def infer_aligned(task):
    old=infer(task)
    options=source_models(task)
    rejected=collections.Counter();passed=[]
    for info in options:
        output=candidate(task,info)
        if output['status']=='ALIGNED_FULL_CONTEXT_CONSENSUS':
            passed.append((info,output))
        else:rejected[output['status']]+=1
    if not passed:
        return {'original':old,'aligned':{'status':'ABSTAIN_NO_ALIGNED_CANDIDATE',
                  'prediction':None,'source_candidates':len(options),
                  'rejection_reasons':dict(rejected)}}
    distinct={tuple(x[1]['prediction']) for x in passed}
    if len(distinct)!=1:
        return {'original':old,'aligned':{'status':'ABSTAIN_MULTIPLE_GENERATOR_OUTPUTS',
                  'prediction':None,'admitted_generators':len(passed),
                  'distinct_outputs':len(distinct)}}
    # Do not claim generator identity unless exactly one candidate has survived.
    # It is safe to report a shared exact query outcome across all retained source candidates,
    # but a source-incompatible true generator may still exist.
    return {'original':old,'aligned':{'status':'ALIGNED_GENERATOR_CONSENSUS',
              'prediction':list(next(iter(distinct))),
              'admitted_generators':len(passed),
              'generator_identity_unique':len(passed)==1,
              'canonical_model_families':[x[1]['models'] for x in passed]}}
