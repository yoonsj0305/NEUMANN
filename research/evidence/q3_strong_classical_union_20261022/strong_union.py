#!/usr/bin/env python3
"""Causal original ARC2 200 task head-to-head: strongest historical classical vs object extension.
Strict independent grader; no original test output in inference job.
"""
import argparse,collections,hashlib,json,pathlib,sys,time
BASE=pathlib.Path(__file__).resolve().parent
NEW=BASE.parent/'q3_object_synthesis_transfer_20261022'
sys.path[:0]=[str(BASE),str(NEW)]
import historical_strong_composer as prior
import object_relational_proposer as addon

def main():
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['infer','grade'],required=True)
 p.add_argument('--masked');p.add_argument('--sealed');p.add_argument('--source')
 p.add_argument('--out',required=True);a=p.parse_args();t=time.perf_counter()
 if a.mode=='infer':
    fs=sorted(pathlib.Path(a.masked).glob('*.json'),key=lambda x:hashlib.sha256(x.stem.encode()).hexdigest())
    assert len(fs)==200
    assert hashlib.sha256(('\n'.join(f.stem for f in fs)+'\n').encode()).hexdigest()=='9f9f9f80d9c51dd31e0ad999e7d2cf7289fcd2791f785ba41fd74d1b86c8dc9b'
    rows={}
    for f in fs:
        task=json.loads(f.read_text())
        assert all('output' not in x for x in task['test'])
        strong=prior.find_programs(task);pbest=prior.choose_program(strong)
        historical=prior.predict(task,pbest)
        added=addon.solve(task)
        proposed=added.get('prediction')
        automatic=historical if historical is not None else proposed
        rows[f.stem]={'strong_original_proposal_count':len(strong),
                       'strong_prediction':historical,'new_operator_status':added['status'],
                       'new_operator_prediction':proposed,
                       'prioritized_automatic_prediction':automatic,
                       'new_operator_ast':added.get('ast')}
    d={'schema':'NEUMANN_STRONGEST_PRIOR_PLUS_OBJECT_PROGRAMS_200.v1',
       'n':200,'test_output_labels_seen':False,'rows':rows,
       'predominant_baseline':'unchanged frozen source historical 96+64 classic DSL',
       'total_inference_wall_s':time.perf_counter()-t}
 else:
    sealed=pathlib.Path(a.sealed);s=json.loads(sealed.read_text())
    assert s['n']==200 and not s['test_output_labels_seen'] and len(s['rows'])==200
    fs=sorted(pathlib.Path(a.source).glob('*.json'),key=lambda x:hashlib.sha256(x.stem.encode()).hexdigest())[800:]
    assert len(fs)==200
    totals=collections.Counter();rows={}
    norm=lambda x:json.dumps(x,separators=(',',':'),sort_keys=True).encode()
    for f in fs:
        d=json.loads(f.read_text());r=s['rows'][f.stem];truth=[q['output'] for q in d['test']]
        def exact(key):return r[key] is not None and len(r[key])==len(truth) and all(x==y for x,y in zip(r[key],truth))
        old=bool(exact('strong_prediction'));new=bool(exact('new_operator_prediction'))
        auto=bool(exact('prioritized_automatic_prediction'))
        totals['historical_correct']+=int(old);totals['new_correct']+=int(new)
        totals['union_oracle_correct']+=int(old or new);totals['deployable_fallback_correct']+=int(auto)
        totals['new_unique_correct']+=int(new and not old)
        if new and not old:
            print('NEW_OVER_STRONGEST_PRIOR',json.dumps({'id':f.stem,'old_program_count':r['strong_original_proposal_count'],
             'new_ast':r['new_operator_ast'],'predicted_sha256':hashlib.sha256(norm(r['new_operator_prediction'])).hexdigest(),
             'source_truth_sha256':hashlib.sha256(norm(truth)).hexdigest()},sort_keys=True),flush=True)
        rows[f.stem]={'strong':old,'object_extension':new,'automatic':auto,'strong_candidate_count':r['strong_original_proposal_count']}
    d={'schema':'NEUMANN_STRONG_PRIOR_UNION_POSTGRADE_200.v1','n':200,'totals':dict(totals),
       'sealed_source_only_sha256':hashlib.sha256(sealed.read_bytes()).hexdigest(),'rows':rows,
       'union_is_hindsight_oracle_not_automatic':True,'is_first_blind':False,
       'global_neural_only_q3':'OPEN','global_frontier_q4_10x':'OPEN'}
    print('CAUSAL_STRONGEST_PRIOR_COMPARE',json.dumps(d['totals'],sort_keys=True),flush=True)
 out=pathlib.Path(a.out);out.parent.mkdir(exist_ok=True,parents=True);out.write_text(json.dumps(d,sort_keys=True)+'\n')
 print('SOURCE_ORIGINAL_VERDICT_SHA256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
