#!/usr/bin/env python3
"""Grade sealed independent original ARC / ConceptARC test labels; never imported by inference."""
import argparse,collections,hashlib,json,pathlib

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--sealed',required=True)
    p.add_argument('--original',required=True)
    p.add_argument('--corpus',choices=['conceptarc160','arc2eval120'],required=True)
    p.add_argument('--out',required=True)
    a=p.parse_args()
    original=pathlib.Path(a.original)
    s=pathlib.Path(a.sealed); before=json.loads(s.read_text())
    n=160 if a.corpus=='conceptarc160' else 120
    assert before['n']==n and before['test_labels_seen'] is False
    tasks={}
    if a.corpus=='conceptarc160':
        categories=sorted(x for x in original.iterdir() if x.is_dir())
        assert len(categories)==16
        for folder in categories:
            fs=sorted(folder.glob('*.json'));assert len(fs)==10
            for f in fs:tasks[folder.name+'__'+f.stem]=json.loads(f.read_text())
        assert len(tasks)==160
    else:
        fs=sorted(original.glob('*.json'));assert len(fs)==120
        tasks={f.stem:json.loads(f.read_text()) for f in fs}
    assert set(tasks)==set(before['rows'])
    sums=collections.Counter();records={}
    for name,original_task in sorted(tasks.items()):
        r=before['rows'][name]
        ground=[q['output'] for q in original_task['test']]
        pred=r.get('prediction')
        ok=bool(pred is not None and len(pred)==len(ground) and all(a==b for a,b in zip(pred,ground)))
        sums[r['status']]+=1;sums['attempted']+=int(pred is not None);sums['exact_correct']+=int(ok)
        if r['status']=='ADAPTIVE_TWO_STEP_AST':
            sums['adaptive_attempted']+=1;sums['adaptive_correct']+=int(ok)
        if r['status'] in ('FROZEN_CLASSICAL','NEW_RELATIONAL_PROGRAM'):
            sums['prior_attempted']+=1;sums['prior_exact_correct']+=int(ok)
        if ok and r['status']=='ADAPTIVE_TWO_STEP_AST':
            v={'original_id':name,'source_demo_count':len(original_task['train']),
               'original_test_count':len(original_task['test']),
               'ast':r['ast'],
               'expected_output_sha256':hashlib.sha256(canonical(ground)).hexdigest(),
               'prediction_sha256':hashlib.sha256(canonical(pred)).hexdigest(),
               'source_search':r['adaptive_search']}
            print('ADAPTIVE_NEW_EXACT_ORIGINAL',json.dumps(v,sort_keys=True),flush=True)
        records[name]={'status':r['status'],'correct':ok,
                       'candidate_was_published':pred is not None}
    sums['problems']=n
    assert sums['prior_exact_correct']+sums['adaptive_correct']==sums['exact_correct']
    doc={'schema':'NEUMANN_ADAPTIVE_TWO_STAGE_INDEPENDENT_ORIGINAL_GRADE.v1',
         'corpus':a.corpus,'pregrade_sha256':hashlib.sha256(s.read_bytes()).hexdigest(),
         'counts':dict(sums),'rows':records,
         'global_frontier_claim':'OPEN','new_neural_primitive_claim':'OPEN',
         'historical_exposure':'same public corpora reused; no pristine first-blind'}
    target=pathlib.Path(a.out);target.parent.mkdir(exist_ok=True,parents=True)
    target.write_text(json.dumps(doc,sort_keys=True)+'\n')
    print('ADAPTIVE_INDEPENDENT_ORIGINAL',a.corpus,json.dumps(doc['counts'],sort_keys=True),
          'score_sha256',hashlib.sha256(target.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
