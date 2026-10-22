"""Fused canonical generator index: same Q3 answers with less work.

Remove unused prior predictor call. Memoize exact de Bruijn W-gram -> unique
ring phase lookup (length W windows uniquely identify phase), fuse generator
compatibility and full source alignment. No original held-out outputs, oracle
metadata, random ranking, or new task source classes.
"""
import collections,functools
from debruijn_structural_model import debruijn
FEATURES=('full','sum','center_outer','center_hist')

@functools.lru_cache(maxsize=48)
def phase_index(k,W):
    cycle=debruijn(k,W)
    n=len(cycle)
    idx={tuple(cycle[(i+j)%n] for j in range(W)):i for i in range(n)}
    assert len(idx)==n
    return cycle,idx

def source_phases(task,k,W):
    cycle,index=phase_index(k,W);length=len(cycle);offsets=[]
    for d in task['train']:
        x=d['input']
        if len(x)<W:return None
        off=index.get(tuple(x[:W]))
        if off is None:return None
        if any(value!=cycle[(off+j)%length] for j,value in enumerate(x)):
            return None
        offsets.append(off)
    return offsets

def signature(w,kind):
    if kind=='full':return w
    if kind=='sum':return (sum(w),)
    middle=len(w)//2
    if kind=='center_outer':return (w[middle],sum(w)-w[middle])
    if kind=='center_hist':
        return (w[middle],tuple(sorted(collections.Counter(w[:middle]+w[middle+1:]).items())))
    raise ValueError(kind)

def infer_fast(task):
    query=task['query']
    input_vals=[v for z in task['train'] for v in z['input']]+list(query)
    if not input_vals:return {'status':'ABSTAIN_EMPTY_INPUT','prediction':None}
    observed=max(input_vals)+1
    source_outputs=[v for z in task['train'] for v in z['output']]
    if not source_outputs:return {'status':'ABSTAIN_EMPTY_TRAINING_OUTPUT','prediction':None}
    lower_k=max(observed,max(source_outputs)+1,2)
    admitted=[];number_of_source_models=0
    for k in range(lower_k,7):
        for W in (3,5,7):
            if k**W>512:continue
            R=(W-1)//2
            if not any(R%r==0 and 1<=R//r<=5 for r in (1,2,3)):continue
            phases=source_phases(task,k,W)
            if phases is None:continue
            number_of_source_models+=1
            if len(query)<2*R+1:continue
            cycle,_=phase_index(k,W);n=len(cycle)
            observations=[]
            for pair,offset in zip(task['train'],phases):
                x=pair['input'];y=pair['output']
                if len(x)!=len(y):
                    observations=[];break
                for j,target in enumerate(y):
                    w=tuple(cycle[(offset+j+t)%n] for t in range(-R,R+1))
                    observations.append((w,target))
            if not observations:continue
            qlen=len(query)
            windows=[tuple(query[(i+t)%qlen] for t in range(-R,R+1)) for i in range(qlen)]
            predictions={}
            for kind in FEATURES:
                table={};valid=True
                for w,target in observations:
                    key=signature(w,kind)
                    if key in table and table[key]!=target:
                        valid=False;break
                    table[key]=target
                if not valid:continue
                keys=[signature(w,kind) for w in windows]
                if all(x in table for x in keys):
                    predictions[kind]=tuple(table[x] for x in keys)
            if not predictions:continue
            possible=set(predictions.values())
            if len(possible)!=1:continue
            admitted.append(next(iter(possible)))
    if not admitted:
        return {'status':'ABSTAIN','prediction':None,
                'matched_generator_classes':number_of_source_models}
    if len(set(admitted))!=1:
        return {'status':'ABSTAIN_GENERATOR_DISAGREEMENT','prediction':None,
                'matched_generator_classes':number_of_source_models}
    return {'status':'MATCHED_SOURCE_GENERATOR_AND_RULE_CONSENSUS',
            'prediction':list(admitted[0]),
            'matched_generator_classes':number_of_source_models,
            'admitted_candidates':len(admitted)}
