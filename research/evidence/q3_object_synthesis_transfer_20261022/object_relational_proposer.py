#!/usr/bin/env python3
"""Source-only typed relational object grammar, with intact historical solver first.
Original test outputs must be physically absent. No neural novelty claim.
"""
import argparse,collections,hashlib,json,pathlib,time
import numpy as np
from frozen_original_typed_selector_v2 import (asarr,regions,d4,mapped,uniform_color_map,task_rules,complexity,predict as baseline_predict)

D4=('id','lr','ud','r90','r180','r270','tr','anti')
OPS=(['identity']+
 [f'pack:{axis}:{kind}:{gap}' for axis in ('h','v') for kind in ('large','small','color','position') for gap in (0,1)]+
 [f'sym-{a}:{mode}' for a in ('lr','ud','both') for mode in ('complete','intersect')]+
 [f'rect:{mode}:{conn}' for mode in ('fill','outline') for conn in (4,8)]+
 [f'connect:{direction}' for direction in ('row','col','both')]+
 [f'foreground:{mode}' for mode in ('box','outline')]+
 [f'reduce:{axis}' for axis in ('rows','cols','both')]+
 [f'rowcol:{kind}' for kind in ('intersection','cross')])

def packed(a,axis,ordering,gap):
    obs=regions(a,4)
    if not obs or len(obs)>12:return None
    if ordering=='large':obs.sort(key=lambda z:(-z['area'],z['top'],z['left']))
    elif ordering=='small':obs.sort(key=lambda z:(z['area'],z['top'],z['left']))
    elif ordering=='color':obs.sort(key=lambda z:(z['color'],z['top'],z['left']))
    else:obs.sort(key=lambda z:(z['top'],z['left']))
    ps=[np.where(o['mask'],a,0)[o['top']:o['bottom']+1,o['left']:o['right']+1] for o in obs]
    if axis=='h':
        h=max(x.shape[0] for x in ps);w=sum(x.shape[1] for x in ps)+gap*(len(ps)-1)
    else:
        w=max(x.shape[1] for x in ps);h=sum(x.shape[0] for x in ps)+gap*(len(ps)-1)
    if not (0<h<=30 and 0<w<=30):return None
    out=np.zeros((h,w),dtype=np.int16);offset=0
    for p in ps:
        if axis=='h':out[:p.shape[0],offset:offset+p.shape[1]]=p;offset+=p.shape[1]+gap
        else:out[offset:offset+p.shape[0],:p.shape[1]]=p;offset+=p.shape[0]+gap
    return out

def operation(inp,op):
    a=asarr(inp);h,w=a.shape
    if op=='identity':return a.copy()
    if op.startswith('pack:'):
        _,axis,order,space=op.split(':');return packed(a,axis,order,int(space))
    if op.startswith('sym-'):
        kind,mode=op.split(':');which=kind[4:]
        other=np.fliplr(a) if which=='lr' else np.flipud(a) if which=='ud' else np.rot90(a,2)
        return np.where(a!=0,a,other) if mode=='complete' else np.where(a==other,a,0)
    if op.startswith('rect:'):
        _,mode,c=op.split(':');out=a.copy()
        for ob in regions(a,int(c)):
            y0,y1,x0,x1=ob['top'],ob['bottom'],ob['left'],ob['right'];v=ob['color']
            if mode=='fill':out[y0:y1+1,x0:x1+1]=v
            else:
                out[y0,x0:x1+1]=v;out[y1,x0:x1+1]=v
                out[y0:y1+1,x0]=v;out[y0:y1+1,x1]=v
        return out
    if op.startswith('connect:'):
        mode=op.split(':')[1];out=a.copy()
        for co in (int(v) for v in np.unique(a) if v!=0):
            if mode in ('row','both'):
                for i in range(h):
                    cols=np.flatnonzero(a[i]==co)
                    if len(cols)>1:out[i,cols[0]:cols[-1]+1]=co
            if mode in ('col','both'):
                for j in range(w):
                    rows=np.flatnonzero(a[:,j]==co)
                    if len(rows)>1:out[rows[0]:rows[-1]+1,j]=co
        return out
    if op.startswith('foreground:'):
        mode=op.split(':')[1];p=np.argwhere(a!=0)
        if not len(p):return None
        y0,x0=p.min(0);y1,x1=p.max(0);v=int(a[tuple(p[0])]);out=a.copy()
        if mode=='box':out[y0:y1+1,x0:x1+1]=v
        else:
            out[y0,x0:x1+1]=v;out[y1,x0:x1+1]=v
            out[y0:y1+1,x0]=v;out[y0:y1+1,x1]=v
        return out
    if op.startswith('reduce:'):
        mode=op.split(':')[1]
        if not np.any(a):return None
        if mode=='rows':return a[np.any(a!=0,axis=1),:]
        if mode=='cols':return a[:,np.any(a!=0,axis=0)]
        if mode=='both':return a[np.any(a!=0,axis=1)][:,np.any(a!=0,axis=0)]
    if op.startswith('rowcol:'):
        mode=op.split(':')[1];out=a.copy()
        for co in (int(z) for z in np.unique(a) if z!=0):
            row=np.any(a==co,axis=1);col=np.any(a==co,axis=0)
            if mode=='intersection':out[np.ix_(row,col)]=co
            else:
                for i in np.flatnonzero(row):out[i,:]=co
                for j in np.flatnonzero(col):out[:,j]=co
        return out
    return None

def proposals(task,max_count=500):
    demos=task['train'];X=[asarr(d['input']) for d in demos];Y=[asarr(d['output']) for d in demos]
    found=[]
    for op in OPS:
        try:z=[operation(x,op) for x in X]
        except (ValueError,IndexError,TypeError):continue
        if any(a is None or not a.size for a in z):continue
        for orient in D4:
            r=[d4(q,orient) for q in z]
            if any(a.shape!=b.shape for a,b in zip(r,Y)):continue
            palette={}
            if not all(uniform_color_map(a,b,palette) for a,b in zip(r,Y)):continue
            if not all(np.array_equal(mapped(a,palette),b) for a,b in zip(r,Y)):continue
            found.append({'operator':op,'orientation':orient,'mapping':palette})
            if len(found)>=max_count:return found
    return found

def rule_cost(p):
    return (3+(2 if p['operator'].startswith('pack:') else 1)+int(p['orientation']!='id')+
            sum(k!=v for k,v in p['mapping'].items()),p['operator'],p['orientation'])

def apply(task,rule):
    results=[]
    for t in task['test']:
        x=operation(t['input'],rule['operator'])
        if x is None:return None
        x=d4(x,rule['orientation']);x=mapped(x,rule['mapping'])
        if x is None or x.size>900:return None
        results.append(x.tolist())
    return results

def solve(task):
    begin=time.perf_counter()
    existing=task_rules(task)
    if existing:
        rule=min(existing,key=complexity)
        return {'status':'FROZEN_CLASSICAL','candidate_count':len(existing),
                'prediction':baseline_predict(task,rule),'ast':rule,'wall_s':time.perf_counter()-begin}
    generated=proposals(task)
    for rule in sorted(generated,key=rule_cost):
        prediction=apply(task,rule)
        if prediction is not None:
            return {'status':'NEW_RELATIONAL_PROGRAM','candidate_count':len(generated),
                    'prediction':prediction,'ast':rule,'wall_s':time.perf_counter()-begin}
    return {'status':'ABSTAIN_NO_PROGRAM','candidate_count':len(generated),
            'prediction':None,'wall_s':time.perf_counter()-begin}

def main():
    p=argparse.ArgumentParser();p.add_argument('--masked-dir',required=True);p.add_argument('--out',required=True)
    p.add_argument('--limit',type=int,default=0);args=p.parse_args();t0=time.perf_counter()
    fs=sorted(pathlib.Path(args.masked_dir).glob('*.json'))
    if args.limit:fs=fs[:args.limit]
    rows={}
    for n,f in enumerate(fs):
        task=json.loads(f.read_text())
        assert all('output' not in x for x in task['test']),f
        try:rows[f.stem]=solve(task)
        except Exception as err:rows[f.stem]={'status':'ERROR','prediction':None,'error':type(err).__name__+': '+str(err)[:200]}
        if (n+1)%20==0:print('PROGRESS',n+1,dict(collections.Counter(q['status'] for q in rows.values())),flush=True)
    d={'schema':'NEUMANN_ORIGINAL_SOURCE_RELATIONAL_PROGRAM_GRAFT.v1','n':len(fs),
       'test_labels_accessed':False,'status_counts':dict(collections.Counter(q['status'] for q in rows.values())),
       'inference_wall_s':time.perf_counter()-t0,'rows':rows}
    out=pathlib.Path(args.out);out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps(d,sort_keys=True,separators=(',',':'))+'\n')
    print('SOURCE_ONLY_PROGRAMS',json.dumps(d['status_counts'],sort_keys=True),'wall',d['inference_wall_s'],
          'sha256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
