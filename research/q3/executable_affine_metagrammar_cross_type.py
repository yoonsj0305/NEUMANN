"""Q3 bounded meta-invention: source-verified ASTs -> automatically induced
affine relations -> unseen-width bitvectors and NEW array typed interpreter.

Self-contained, STANDARD LIBRARY ONLY. All task families are synthetic and
human-designed, never claim global Q3/Q4/Q6 from this smoke/causality gate.
"""
import hashlib
import itertools
import json
import random
import time
from pathlib import Path

def calc(ast,x,n):
    mask=(1<<n)-1;op=ast[0]
    if op=='x':return x
    if op=='shl':return (calc(ast[1],x,n)<<ast[2])&mask
    if op=='shr':return calc(ast[1],x,n)>>ast[2]
    if op=='xor':return calc(ast[1],x,n)^calc(ast[2],x,n)
    if op=='or':return calc(ast[1],x,n)|calc(ast[2],x,n)
    if op=='add':return (calc(ast[1],x,n)+calc(ast[2],x,n))&mask
    if op=='and':return calc(ast[1],x,n)&calc(ast[2],x,n)
    raise ValueError('unknown opcode')

def secret_teacher(x,n,k,family):
    a=(x<<k)&((1<<n)-1)
    b=x>>(n-k if family=='complement' else k)
    return a^b

def source_examples(n,k,family):
    xs=(0,1,2,3,5,7,9,11,13,15,21,29,43,59,71,97)
    return [(x,secret_teacher(x,n,k,family)) for x in xs if x<(1<<n)]

def ast_stream(n):
    x=('x',);shifts=[]
    for j in range(1,n):
        shifts.extend([('shl',x,j),('shr',x,j)])
    yield x
    for p in shifts:yield p
    for p in shifts:
        for q in shifts:
            for op in ('xor','and','add','or'):
                yield (op,p,q)

def source_ok(ast,n,data):
    return all(calc(ast,x,n)==y for x,y in data)

def exact(ast,n,k,family):
    return all(calc(ast,x,n)==secret_teacher(x,n,k,family) for x in range(1<<n))

def cold_bit(n,data,oracle):
    checked=0
    for p in ast_stream(n):
        checked+=1
        if source_ok(p,n,data) and oracle(p):
            return p,checked
    return None,checked

def method_invention(source):
    rows=[]
    for n,p in source:
        if p[0] not in ('xor','or','add','and'):raise ValueError('root mismatch')
        a,b=p[1:]
        if a[0]=='shr' and b[0]=='shl':a,b=b,a
        if (a[0],b[0])!=('shl','shr'):raise ValueError('unsupported source AST')
        rows.append((n,a[2],b[2],p[0]))
    if len(set(z[3] for z in rows))!=1:raise ValueError('root not reusable')
    proposals=[]
    for a,b,c in itertools.product(range(-2,3),range(-2,3),range(-12,13)):
        supp=frozenset(i for i,(n,left,right,_) in enumerate(rows)
                       if a*n+b*left+c==right)
        if len(supp)<5:continue
        if len(set(rows[i][0] for i in supp))<2:continue
        if len(set(rows[i][1] for i in supp))<3:continue
        proposals.append(((a,b,c),supp,abs(a)+abs(b)+abs(c)))
    universe=set(range(len(rows)))
    chosen=None
    for k in (1,2,3):
        candidates=[]
        for group in itertools.combinations(proposals,k):
            cover=set().union(*(part[1] for part in group))
            if cover==universe:
                candidates.append((sum(part[2] for part in group),
                   tuple(part[0] for part in group)))
        if candidates:
            chosen=min(candidates)[1];break
    if not chosen:raise ValueError('no inferred constructor family')
    method={'kind':'ExecutableAffineRelationConstructor','root':rows[0][3],
            'relations':[list(t) for t in chosen],'source_widths':[4,6],
            'source_program_count':len(rows),'human_defined_interpreter':True}
    method['sha256']=hashlib.sha256(
       json.dumps(method,sort_keys=True).encode()).hexdigest()
    return method

def learned_bit_candidates(method,n):
    seen=set()
    for a,b,c in method['relations']:
        for l in range(1,n):
            r=a*n+b*l+c
            if not 1<=r<n:continue
            p=(method['root'],('shl',('x',),l),('shr',('x',),r))
            if p not in seen:
                seen.add(p);yield p

def learned_bit(n,data,method,oracle):
    count=0
    for p in learned_bit_candidates(method,n):
        count+=1
        if source_ok(p,n,data) and oracle(p):
            return p,count
    return None,count

def segment(x,start,length):
    if start<0 or length<0:return None
    return tuple(x[i] if i<len(x) else None
                 for i in range(start,start+length))

def array_teacher(x,k,family):
    return tuple(x[k:] if family=='complement' else x[k:2*k])

def array_training(n,k,family):
    seed=int(hashlib.sha256(f'{n}-{k}-{family}'.encode()).hexdigest()[:12],16)
    rng=random.Random(seed);data=[]
    for i in range(18):
        xs=tuple(rng.randrange(11) for _ in range(n+i%5))
        data.append((xs,array_teacher(xs,k,family)))
    return data

def array_fit(candidate,data):
    a,b,c,start=candidate
    return all(segment(x,start,a*len(x)+b*start+c)==y for x,y in data)

def memory_array(method):
    for a,b,c in method['relations']:
        for start in range(1,8):
            yield (a,b,c,start)

def classical_array_mdl():
    coeff=list(itertools.product(range(-2,3),range(-2,3),range(-12,13)))
    coeff.sort(key=lambda p:(
      sum(abs(v) for v in p),sum(v!=0 for v in p),
      abs(p[2]),abs(p[0]),abs(p[1]),p))
    for a,b,c in coeff:
        for start in range(1,8):
            yield (a,b,c,start)

def array_solve(data,mode,method):
    checked=0;started=time.perf_counter_ns()
    source=memory_array(method) if mode=='memory' else classical_array_mdl()
    for p in source:
        checked+=1
        if array_fit(p,data):
            return p,checked,time.perf_counter_ns()-started
    return None,checked,time.perf_counter_ns()-started

def array_test(n,k,family,p):
    if p is None:return False
    seed=int(hashlib.sha256(f'holdout:{n}:{k}:{family}'.encode()).hexdigest()[:12],16)
    rng=random.Random(seed);a,b,c,start=p
    for i in range(250):
        x=tuple(rng.randrange(-100,101) for _ in range(n+i%6))
        if segment(x,start,a*len(x)+b*start+c)!=array_teacher(x,k,family):
            return False
    return True

def main():
    start=time.perf_counter_ns();source=[];source_cost=0
    for family in ('complement','same-index'):
        for n in (4,6):
            for hidden_k in range(1,n):
                data=source_examples(n,hidden_k,family)
                t=time.perf_counter_ns()
                p,_=cold_bit(n,data,lambda x,n=n,k=hidden_k,f=family:
                            exact(x,n,k,f))
                source_cost+=time.perf_counter_ns()-t
                if p is None:raise AssertionError('source program not proven')
                source.append((n,p))
    t=time.perf_counter_ns();method=method_invention(source)
    source_cost+=time.perf_counter_ns()-t
    assert set(map(tuple,method['relations']))=={(0,1,0),(1,-1,0)}
    finite=[];arrays=[]
    for family in ('complement','same-index'):
        for n in (8,9,10):
            for hidden_k in range(1,n):
                data=source_examples(n,hidden_k,family)
                oracle=lambda p,n=n,k=hidden_k,f=family:exact(p,n,k,f)
                ml,mc=learned_bit(n,data,method,oracle)
                cl,cc=cold_bit(n,data,oracle)
                finite.append({'width':n,'private_family':family,'private_k':hidden_k,
                               'memory_checks':mc,'cold_checks':cc,
                               'both_full_exact':ml is not None and cl is not None})
        for n in range(16,21):
            for hidden_k in range(1,8):
                data=array_training(n,hidden_k,family)
                pm,mchecks,mtime=array_solve(data,'memory',method)
                pc,cchecks,ctime=array_solve(data,'classical',method)
                arrays.append({'length':n,'private_family':family,'private_k':hidden_k,
                  'memory_checks':mchecks,'classical_checks':cchecks,
                  'memory_ns':mtime,'classical_ns':ctime,
                  'memory_exact':array_test(n,hidden_k,family,pm),
                  'classical_exact':array_test(n,hidden_k,family,pc)})
    ablations=[]
    for relation in method['relations']:
        narrower={**method,'relations':[relation]}
        correct=0
        for row in finite:
            n=row['width'];k=row['private_k'];f=row['private_family']
            data=source_examples(n,k,f)
            p,_=learned_bit(n,data,narrower,lambda x,n=n,k=k,f=f:exact(x,n,k,f))
            correct+=p is not None
        ablations.append({'rule':relation,'solved':correct})
    ood=[]
    for n in (16,18,20):
        x=tuple(range(n))
        odd=[(x,tuple(reversed(x))),(x[::-1],x)]
        result,_,_=array_solve(odd,'memory',method)
        ood.append(result is None)
    summary={'source_programs':len(source),'new_relations':len(method['relations']),
       'new_width_bitvector_full_exact':sum(x['both_full_exact'] for x in finite),
       'new_width_bitvector_tasks':len(finite),
       'array_meta_exact':sum(x['memory_exact'] for x in arrays),
       'array_cold_exact':sum(x['classical_exact'] for x in arrays),
       'array_tasks':len(arrays),'heldout_per_array_task':250,
       'target_meta_checks':sum(x['memory_checks'] for x in arrays),
       'target_cold_checks':sum(x['classical_checks'] for x in arrays),
       'source_cost_ns':source_cost,
       'raw_array_meta_time_ns':sum(x['memory_ns'] for x in arrays),
       'raw_array_cold_time_ns':sum(x['classical_ns'] for x in arrays),
       'ood_abstain':sum(ood),'single_relation_ablations':ablations,
       'elapsed_ns':time.perf_counter_ns()-start}
    assert summary['new_width_bitvector_full_exact']==48
    assert summary['array_meta_exact']==70 and summary['array_cold_exact']==70
    assert summary['ood_abstain']==len(ood)==3
    output={'schema':'neumann.q3.typed-relational-metagrammar-synthetic-ci-v1',
      'scientific_status':'BOUNDED_SYNTHETIC_ONLY_GLOBAL_Q3_OPEN',
      'learned_method':method,'bitvector':finite,'arrays':arrays,
      'summary':summary,
      'limits':'All tasks/DSL/interpreters and relation hypothesis class are human authored. Strong classical has the same hypothesis class; this is not an independent-author original-first gate or a general Q3/Q4 PASS.'}
    Path('Q3_CROSS_TYPE_EXECUTABLE_CI.json').write_text(json.dumps(output,indent=2))
    print(json.dumps({'method_sha256':method['sha256'],'summary':summary},indent=2))
if __name__=='__main__':main()
