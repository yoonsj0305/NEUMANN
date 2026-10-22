#!/usr/bin/env python3
"""Exact original grammar semantic-equivalence + paired CPU cost; labels not read."""
import argparse,hashlib,json,pathlib,statistics,time,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import relational_pipeline as full
import relational_pipeline_shape_cached as specialized

def digest(rules):return hashlib.sha256(json.dumps(rules,sort_keys=True).encode()).hexdigest()
def task(file):
    d=json.loads(file.read_text())
    assert all('output' not in q for q in d['test']),file.name
    return {'train':d['train'],'test':[{'input':q['input']} for q in d['test']]}
def main():
    a=argparse.ArgumentParser();a.add_argument('--masked',required=True);a.add_argument('--out',required=True);a.add_argument('--pairs',type=int,default=3);x=a.parse_args()
    d=pathlib.Path(x.masked);files=sorted(d.glob('*.json'),key=lambda f:hashlib.sha256(f.stem.encode()).hexdigest());assert len(files)==1000
    dev=files[:800:20];hold=files[800:];assert len(dev)==40 and len(hold)==200
    trials=[]
    for trial in range(x.pairs):
        for method,mod in (([('full',full),('shape_cache',specialized)] if trial%2==0 else [('shape_cache',specialized),('full',full)])):
            start=time.perf_counter();digs=[];n=0
            for f in dev:
                r=mod.task_rules(task(f));digs.append(digest(r));n+=len(r)
            t=time.perf_counter()-start
            trials.append({'trial':trial,'method':method,'wall_s':t,'num_demo_consistent_programs':n,'sha256_per_source_task':hashlib.sha256(('\n'.join(digs)+'\n').encode()).hexdigest()})
            print('ABBA',trial,method,round(t,6),'CANDIDATES',n,flush=True)
    assert len(set(r['sha256_per_source_task'] for r in trials))==1,'non-equivalent ASTs'
    checks=[];start=time.perf_counter()
    for i,f in enumerate(hold):
        t=task(f)
        a=full.task_rules(t);b=specialized.task_rules(t)
        assert a==b,f.name
        checks.append({'id':f.stem,'candidate_count':len(a),'candidate_sha256':digest(a)})
        if (i+1)%50==0:print('EQUIVALENCE_HOLDOUT',i+1,round(time.perf_counter()-start,3),flush=True)
    base=statistics.median(x['wall_s'] for x in trials if x['method']=='full')
    better=statistics.median(x['wall_s'] for x in trials if x['method']=='shape_cache')
    payload={'status':'EXACT_ALL_CANDIDATES_EQUIVALENCE','n_dev_timing':40,'n_holdout_semantic_equality':200,'only_source_masked_test_inputs':True,'task_order_sha':hashlib.sha256(('\n'.join(x['id'] for x in checks)+'\n').encode()).hexdigest(),'median_full_s':base,'median_shape_guarded_cached_s':better,'proposer_speedup':base/better,'measurement_scope':'candidate_proposer only; not full inference or frontier 10x','holdout_checks':checks,'trials':trials,'all_holdout_equal':True,'all_dev_equal':True,'candidate_count_holdout':sum(x['candidate_count'] for x in checks)}
    p=pathlib.Path(x.out);p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(payload,sort_keys=True,indent=2))
    print('SCIENTIFIC_VERDICT',json.dumps({k:v for k,v in payload.items() if k not in ('trials','holdout_checks')}),flush=True)
if __name__=='__main__':main()
