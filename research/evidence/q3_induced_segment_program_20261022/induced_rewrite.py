#!/usr/bin/env python3
"""Induce small conditional sequence programs from task demonstrations, never test answers.

Finite operator *syntax* is authored, parameters are inferred exclusively from demos.
A novel learned neural primitive is NOT claimed. This is exact classical induction.
Task-category and filename are forbidden as inputs to the solver.
"""
import collections,hashlib,json,math,time

def runs(x):
    out=[];i=0
    while i<len(x):
        j=i+1
        while j<len(x) and x[j]==x[i]:j+=1
        if x[i]!=0:out.append((i,j,x[i]))
        i=j
    return out

def translate(x,sub,d,preserve=False):
    n=len(x);v=[0]*n
    keep=set()
    if preserve:keep={i for i in range(n) if i not in sub and x[i]!=0}
    for i in keep:v[i]=x[i]
    for i in sub:
        j=i+d
        if j<0 or j>=n:return None
        if j in keep:return None
        v[j]=x[i]
    return v

def main_run(x):
    r=runs(x)
    if not r:return None
    return sorted(r,key=lambda t:(-(t[1]-t[0]),t[0]))[0]

def apply(x,operator,param=None):
    x=list(x);n=len(x);r=runs(x);o=x.copy()
    if not n or n>100:return None
    if operator=='translate_all':
        return translate(x,[i for i,v in enumerate(x) if v],param)
    if operator=='translate_main':
        q=main_run(x)
        if q is None:return None
        return translate(x,range(q[0],q[1]),param,True)
    if operator=='reverse_nonzero':
        ix=[i for i,v in enumerate(x) if v]
        if not ix:return None
        a,b=ix[0],ix[-1]+1;o[a:b]=o[a:b][::-1];return o
    if operator=='reverse_runs':
        for a,b,c in r:o[a:b]=o[a:b][::-1]
        return o
    if operator=='hollow_runs':
        for a,b,c in r:
            if b-a>=3:o[a+1:b-1]=[0]*(b-a-2)
        return o
    if operator=='span_same_color':
        for c in sorted({c for _,_,c in r}):
            p=[i for i,v in enumerate(x) if v==c]
            if len(p)>1:o[p[0]:p[-1]+1]=[c]*(p[-1]-p[0]+1)
        return o
    if operator=='fill_pairs':
        parity=param
        for c in sorted({c for _,_,c in r}):
            rr=[(a,b) for a,b,co in r if co==c]
            for t in range(parity,len(rr)-1,2):
                a,b=rr[t];u,v=rr[t+1]
                if all(z==0 for z in x[b:u]):o[b:u]=[c]*(u-b)
        return o
    if operator=='expand_short_to_longest':
        if not r:return None
        length=max(b-a for a,b,c in r)
        for a,b,c in r:
            if b-a==length:continue
            target=a if param=='left' else b-length if param=='right' else a-(length-(b-a))//2
            if target<0 or target+length>n:return None
            if any(x[j]!=0 and not a<=j<b for j in range(target,target+length)):return None
            o[a:b]=[0]*(b-a);o[target:target+length]=[c]*length
        return o
    if operator=='copy_longest_to_short':
        if not r:return None
        source=max(r,key=lambda t:(t[1]-t[0],-t[0]))
        width=source[1]-source[0];pattern=x[source[0]:source[1]]
        for a,b,c in r:
            if a==source[0] and b==source[1]:continue
            if b-a>=width:continue
            dest=a if param=='left' else b-width if param=='right' else a-(width-(b-a))//2
            if dest<0 or dest+width>n:return None
            if any(x[j]!=0 and not a<=j<b for j in range(dest,dest+width)):return None
            o[a:b]=[0]*(b-a);o[dest:dest+width]=pattern
        return o
    if operator=='mirror_about_singleton':
        if not r:return None
        single=[a for a,b,c in r if b-a==1]
        if len(single)!=1:return None
        marker=single[0];o=[0]*n;o[marker]=x[marker]
        for i,v in enumerate(x):
            if not v or i==marker:continue
            j=2*marker-i
            if not 0<=j<n or j==marker:return None
            o[j]=v
        return o
    if operator=='duplicate_reflect':
        if not r:return None
        single=[a for a,b,c in r if b-a==1]
        if len(single)!=1:return None
        marker=single[0];o=x.copy()
        for i,v in enumerate(x):
            if not v or i==marker:continue
            j=2*marker-i
            if not 0<=j<n:return None
            if o[j] and o[j]!=v:return None
            o[j]=v
        return o
    if operator=='recolor_by_run_length':
        if not isinstance(param,dict):return None
        for a,b,c in r:o[a:b]=[param.get(b-a,c)]*(b-a)
        return o
    if operator=='recolor_by_index':
        if not isinstance(param,dict):return None
        for rank,(a,b,c) in enumerate(r):o[a:b]=[param.get(rank,c)]*(b-a)
        return o
    if operator=='move_until_marker':
        if not r:return None
        q=main_run(x);other=[(a,b,c) for a,b,c in r if (a,b,c)!=q and b-a==1]
        if q is None or len(other)!=1:return None
        mark=other[0][0]
        if param=='before':target=mark-(q[1]-q[0])
        else:target=mark+1
        if target<0 or target+q[1]-q[0]>n:return None
        return translate(x,range(q[0],q[1]),target-q[0],True)
    if operator=='reflect_single_longest':
        q=main_run(x)
        if q is None:return None
        a,b,c=q;o[a:b]=list(reversed(x[a:b]));return o
    return None

# This list is source-code frozen before the separate evaluator reads target labels.
SIMPLE=('reverse_nonzero','reverse_runs','hollow_runs','span_same_color',
        'mirror_about_singleton','duplicate_reflect','reflect_single_longest')
def learn_color_map(demos,feature):
    mapping={}
    for x,y in demos:
        rr=runs(x); o=runs(y)
        if len(x)!=len(y) or len(rr)!=len(o):return None
        for index,((a,b,c),(ay,by,cy)) in enumerate(zip(rr,o)):
            if (a,b)!=(ay,by):return None
            key=(b-a if feature=='length' else index)
            if key in mapping and mapping[key]!=cy:return None
            mapping[key]=cy
    return mapping if mapping else None

def proposals(demos):
    # All parameters learned by exact fitting to ALL training demonstration pairs.
    parameters=[(z,None) for z in SIMPLE]
    parameters+= [('fill_pairs',p) for p in (0,1)]
    parameters+= [('expand_short_to_longest',s) for s in ('left','right','center')]
    parameters+= [('copy_longest_to_short',s) for s in ('left','right','center')]
    parameters+= [('move_until_marker',s) for s in ('before','after')]
    for d in range(-15,16):
        if d:parameters.extend([('translate_all',d),('translate_main',d)])
    for kind,feat in (('recolor_by_run_length','length'),('recolor_by_index','ordinal')):
        m=learn_color_map(demos,feat)
        if m is not None:parameters.append((kind,m))
    result=[]
    for kind,param in parameters:
        if all(apply(x,kind,param)==y for x,y in demos):
            result.append((kind,param))
    return result

def run(task):
    start=time.perf_counter()
    demos=[]
    for z in task['train']:
        xx=z['input'];yy=z['output']
        if len(xx)!=1 or len(yy)!=1 or not xx[0] or not yy[0] or len(xx[0])!=len(yy[0]):
            return {'status':'UNSUPPORTED_SHAPE','prediction':None,'total_s':time.perf_counter()-start}
        demos.append((xx[0],yy[0]))
    if len(demos)<2:return {'status':'ABSTAIN_NO_CROSS_DEMO','prediction':None,'total_s':time.perf_counter()-start}
    possible=proposals(demos)
    if not possible:return {'status':'ABSTAIN_NO_PROGRAM','prediction':None,'total_s':time.perf_counter()-start}
    candidates=[]
    for typ,param in possible:
        outs=[];valid=True
        for t in task['test']:
            g=t['input']
            if len(g)!=1:valid=False;break
            y=apply(g[0],typ,param)
            if y is None:valid=False;break
            outs.append([y])
        if valid:candidates.append((typ,param,outs))
    if not candidates:return {'status':'ABSTAIN_INVALID_ON_TEST_INPUT','prediction':None,
                              'demo_program_count':len(possible),'total_s':time.perf_counter()-start}
    # Semantics-first abstention when candidate programs disagree on test predictions.
    distinct={}
    for typ,param,outputs in candidates:
        key=json.dumps(outputs,separators=(',',':'))
        distinct.setdefault(key,[]).append((typ,param))
    if len(distinct)!=1:
        return {'status':'ABSTAIN_SEMANTIC_AMBIGUITY','prediction':None,
                'demo_program_count':len(possible),'test_equivalence_classes':len(distinct),
                'total_s':time.perf_counter()-start}
    typ,param,outputs=candidates[0]
    return {'status':'INDUCED_CONSENSUS','prediction':outputs,'induced_kind':typ,
            'induced_parameter':param,'demo_program_count':len(possible),
            'equivalent_test_program_count':len(candidates),'test_equivalence_classes':1,
            'total_s':time.perf_counter()-start}
