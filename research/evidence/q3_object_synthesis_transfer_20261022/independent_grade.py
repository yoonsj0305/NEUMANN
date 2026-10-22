#!/usr/bin/env python3
"""Independent after-prediction original source scorer; never imported in proposing job."""
import argparse,collections,hashlib,json,pathlib
def main():
 p=argparse.ArgumentParser();p.add_argument('--sealed',required=True);p.add_argument('--source-root',required=True);p.add_argument('--out',required=True)
 a=p.parse_args();root=pathlib.Path(a.source_root);before=pathlib.Path(a.sealed)
 original_sha=hashlib.sha256(before.read_bytes()).hexdigest();prediction=json.loads(before.read_text())
 assert prediction['test_labels_accessed'] is False and prediction['n']==320
 all_ids=set(prediction['rows']);totals={};rows={}
 for subset,n in [('evaluation',120),('training',200)]:
    data=sorted((root/subset).glob('*.json')); ids=sorted(x.stem for x in data)
    if subset=='training':
        byhash=sorted(ids,key=lambda x:hashlib.sha256(x.encode()).hexdigest())
        data=[root/subset/(x+'.json') for x in byhash[800:]]
        assert hashlib.sha256(('\n'.join(byhash[800:])+'\n').encode()).hexdigest()=='9f9f9f80d9c51dd31e0ad999e7d2cf7289fcd2791f785ba41fd74d1b86c8dc9b'
    assert len(data)==n
    tally=collections.Counter()
    for f in data:
        assert f.stem in all_ids,f.stem
        d=json.loads(f.read_text()); r=prediction['rows'][f.stem]
        y=[z['output'] for z in d['test']]
        has=r['prediction'] is not None
        good=bool(has and len(y)==len(r['prediction']) and all(x==q for x,q in zip(r['prediction'],y)))
        tally[r['status']]+=1
        tally['predicted']+=int(has);tally['correct']+=int(good)
        if r['status']=='NEW_RELATIONAL_PROGRAM':
            tally['new_operator_attempts']+=1
            tally['new_operator_exact_correct']+=int(good)
            if good:
                normalized=lambda x:json.dumps(x,sort_keys=True,separators=(',',':')).encode()
                print('NEW_ORIGINAL_SOURCE_EXACT_PROGRAM',json.dumps({'subset':subset,'original_id':f.stem,'ast':r.get('ast'),'predicted_target_sha256':hashlib.sha256(normalized(r['prediction'])).hexdigest(),'independent_ground_truth_sha256':hashlib.sha256(normalized(y)).hexdigest(),'test_grid_count':len(y),'source_demo_count':len(d['train'])},sort_keys=True),flush=True)
        if r['status']=='FROZEN_CLASSICAL':
            tally['baseline_attempts']+=1
            tally['baseline_exact_correct']+=int(good)
        rows[f.stem]={'status':r['status'],'exact_correct':good,
                      'candidate_count':r.get('candidate_count',0)}
    totals[subset]=dict(tally)
    assert tally['predicted']<=n
    print('INDEPENDENT_SOURCE_EXACT',subset,json.dumps(totals[subset],sort_keys=True),flush=True)
 out={'schema':'NEUMANN_SOURCE_ORIGINAL_320_HEAD2HEAD_INDEPENDENT_SCORE.v1',
      'source_ref':'ARC-AGI-2 f3283f727488ad98fe575ea6a5ac981e4a188e49',
      'sealed_pregrade_sha256':original_sha,'subset_counts':totals,'graded_originals':rows,
      'pristine_world_first_blind':False,'new_learned_operator_claim':'NOT_SUPPORTED',
      'q3_general_capability_claim':'SCOPED_ONLY_IF_NEW_CASES_CORRECT',
      'frontier_q4_total10x':'OPEN'}
 dest=pathlib.Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(out,sort_keys=True)+'\n')
 print('GRADE_RECEIPT_SHA256',hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
