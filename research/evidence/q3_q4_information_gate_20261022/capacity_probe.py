#!/usr/bin/env python3
"""Q3/Q4 exact input information diagnostic, authentic ARC tasks, zero test-label access.

Theorem: F(u)=F(v), y(u)!=y(v) makes any deterministic f(F) unfit on demos.
Adding PREDEFINED row/column and connected-component summaries is a classical
counterfactual, NOT learned invention or a solved-test claim.
"""
import argparse, collections, hashlib, json, math, pathlib, sys, time
import numpy as np
BASE=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(BASE/'research/evidence/q0_learned_local_structure_20261022'))
from learned_local_rule import features

def appended(g):
    a=np.asarray(g,dtype=np.int32); h,w=a.shape
    common=collections.Counter(a.ravel().tolist()).most_common(1)[0][0]
    per=[]; cc=np.zeros((h,w,4),dtype=np.int32); visited=np.zeros((h,w),bool)
    for y in range(h):
        for x in range(w):
            c=int(a[y,x])
            per.append((int(np.sum(a[y,:]==c)),int(np.sum(a[:,x]==c)),
                        int(np.sum(a[y,:]!=common)),int(np.sum(a[:,x]!=common)),
                        int(a[y,w-1-x]==c),int(a[h-1-y,x]==c)))
            if visited[y,x]: continue
            q=[(y,x)];visited[y,x]=True;pts=[]
            while q:
                i,j=q.pop();pts.append((i,j))
                for di,dj in ((-1,0),(1,0),(0,-1),(0,1)):
                    yy,xx=i+di,j+dj
                    if 0<=yy<h and 0<=xx<w and not visited[yy,xx] and a[yy,xx]==c:
                        visited[yy,xx]=True;q.append((yy,xx))
            ys=[p[0] for p in pts];xs=[p[1] for p in pts]
            sign=(len(pts),max(ys)-min(ys)+1,max(xs)-min(xs)+1,int(min(ys)==0 or min(xs)==0))
            for i,j in pts: cc[i,j]=sign
    return np.asarray(per,dtype=np.float32),cc.reshape(h*w,4).astype(np.float32)

def certify(X,y):
    groups={};first=None
    for idx,(row,label) in enumerate(zip(X,y)):
        key=row.tobytes();lab=int(label)
        if key not in groups:groups[key]={'labels':set(),'first':(idx,lab)}
        g=groups[key]
        if g['labels'] and lab not in g['labels'] and first is None:
            first={'indices':[g['first'][0],idx],'distinct_labels':[g['first'][1],lab],
                   'identical_feature_sha256':hashlib.sha256(key).hexdigest()}
        g['labels'].add(lab)
    conflicts=[v for v in groups.values() if len(v['labels'])>1]
    return {'conflicting_groups':len(conflicts),
            'min_required_additional_bits_lower_bound':max(
              [math.log2(len(v['labels'])) for v in conflicts],default=0.0),
            'exact_source_witness':first}

def analyze(d):
    ds=d['train']
    if not ds or any(np.shape(s['input'])!=np.shape(s['output']) for s in ds):
        return {'status':'SHAPE_CHANGE','proofs':None}
    if sum(len(s['input'])*len(s['input'][0]) for s in ds)>3500:
        return {'status':'DEMO_CAP','proofs':None}
    old=[];row=[];obj=[];targets=[]
    for s in ds:
        X=features(s['input']);R,O=appended(s['input'])
        old.append(X);row.append(R);obj.append(O)
        targets.append(np.asarray(s['output'],np.int32).ravel())
    O=np.concatenate(old);R=np.concatenate(row);C=np.concatenate(obj);Y=np.concatenate(targets)
    proof={k:certify(x,Y) for k,x in (
       ('base',O),('base_plus_rowcol',np.column_stack((O,R))),
       ('base_plus_components',np.column_stack((O,C))),
       ('base_plus_both',np.column_stack((O,R,C))))}
    base=proof['base']['conflicting_groups']
    return {'status':'EVALUATED','proofs':proof,
            'was_impossible_with_original_features':base>0,
            'representation_conflict_resolved_by_rowcol':base>0 and proof['base_plus_rowcol']['conflicting_groups']==0,
            'representation_conflict_resolved_by_components':base>0 and proof['base_plus_components']['conflicting_groups']==0,
            'representation_conflict_resolved_by_both':base>0 and proof['base_plus_both']['conflicting_groups']==0}

def main():
    p=argparse.ArgumentParser();p.add_argument('--masked-root',required=True);p.add_argument('--out',required=True)
    args=p.parse_args();root=pathlib.Path(args.masked_root);beg=time.perf_counter()
    allrows={};stats={}
    for split,n in [('training',1000),('evaluation',120)]:
        paths=sorted((root/split).glob('*.json'));assert len(paths)==n,(split,len(paths))
        rows={}
        for f in paths:
            d=json.loads(f.read_text());assert all('output' not in t for t in d['test']),f.name
            result=analyze(d)
            result['train_content_sha256']=hashlib.sha256(json.dumps(d['train'],sort_keys=True).encode()).hexdigest()
            rows[f.stem]=result
        allrows[split]=rows
        relevant=[r for r in rows.values() if r['status']=='EVALUATED']
        bad=[r for r in relevant if r['was_impossible_with_original_features']]
        stats[split]={'source_total':n,'eligible':len(relevant),'fixed_original_feature_impossible':len(bad),
                      'fixed_original_feature_can_fit_information':len(relevant)-len(bad),
                      'rowcol_repairs':sum(r['representation_conflict_resolved_by_rowcol'] for r in bad),
                      'component_repairs':sum(r['representation_conflict_resolved_by_components'] for r in bad),
                      'combined_repairs':sum(r['representation_conflict_resolved_by_both'] for r in bad),
                      'still_impossible_after_both':sum(r['proofs']['base_plus_both']['conflicting_groups']>0 for r in bad),
                      'shape_change':sum(r['status']=='SHAPE_CHANGE' for r in rows.values()),
                      'demo_cap':sum(r['status']=='DEMO_CAP' for r in rows.values())}
        print('ORIGINAL_SOURCE_EXACT_INFO_GATE',split,json.dumps(stats[split],sort_keys=True),flush=True)
    d={'schema':'NEUMANN_Q3_Q4_SOURCE_ORIGINAL_EXACT_INFORMATION_BOUND.v1',
       'test_output_labels_available_to_probe':False,
       'source':'ARC-AGI-2 official f3283f727488ad98fe575ea6a5ac981e4a188e49',
       'global_Q3_novel_learned_operator':'OPEN','global_Q4_10x':'OPEN',
       'scope':'classical predefined features; repairs only DEMONSTRATION representability; NOT tested generalization',
       'wall_s':time.perf_counter()-beg,'stats':stats,'source_rows':allrows}
    pathlib.Path(args.out).write_text(json.dumps(d,sort_keys=True,separators=(',',':'))+'\n')
    print('EXACT_SOURCE_CERTIFICATE_SHA256',hashlib.sha256(pathlib.Path(args.out).read_bytes()).hexdigest())
if __name__=='__main__':main()
