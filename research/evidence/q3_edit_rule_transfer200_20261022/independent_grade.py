#!/usr/bin/env python3
"""After-seal exact scorer of ALL original 200 tasks, independent original labels only."""
import argparse,collections,hashlib,json,pathlib
def main():
 p=argparse.ArgumentParser();p.add_argument('--sealed',required=True);p.add_argument('--source',required=True);p.add_argument('--out',required=True)
 a=p.parse_args();sf=pathlib.Path(a.sealed);pre=json.loads(sf.read_text())
 assert pre['n']==200 and not pre['test_labels_seen']
 root=pathlib.Path(a.source);files=sorted(root.glob('*.json'),key=lambda f:hashlib.sha256(f.stem.encode()).hexdigest())
 assert len(files)==1000;files=files[800:]
 assert hashlib.sha256(('\n'.join(f.stem for f in files)+'\n').encode()).hexdigest()=='9f9f9f80d9c51dd31e0ad999e7d2cf7289fcd2791f785ba41fd74d1b86c8dc9b'
 assert {f.stem for f in files}==set(pre['rows'])
 counts=collections.Counter();scores={}
 norm=lambda x:json.dumps(x,sort_keys=True,separators=(',',':')).encode()
 for f in files:
    task=json.loads(f.read_text());r=pre['rows'][f.stem]
    pred=r.get('prediction');truth=[x['output'] for x in task['test']]
    valid=bool(pred is not None and len(pred)==len(truth) and all(p==t for p,t in zip(pred,truth)))
    counts['correct']+=int(valid);counts['attempted']+=int(pred is not None);counts[r['status']]+=1
    if r['status']=='STRONG_HISTORICAL_CLASSICAL':counts['strong_classical_correct']+=int(valid)
    elif valid:
        counts['new_beyond_strongest_correct']+=1
        if r['status']=='INFERRED_RELATIONAL_EDIT_RULE':counts['mask_learner_correct']+=1
        print('NEW_ADAPTIVE_OVER_STRONGEST_CLASSICAL',json.dumps({'id':f.stem,'status':r['status'],
          'ast':r.get('ast'),'prediction_sha256':hashlib.sha256(norm(pred)).hexdigest(),
          'source_truth_sha256':hashlib.sha256(norm(truth)).hexdigest(),
          'demonstrations':len(task['train'])},sort_keys=True),flush=True)
    scores[f.stem]={'status':r['status'],'correct':valid,'prediction_sent':pred is not None}
 assert counts['correct']==counts['strong_classical_correct']+counts['new_beyond_strongest_correct']
 assert counts['correct']<=200
 result={'schema':'NEUMANN_Q3_ADAPTIVE_SOURCE200_INDEPENDENT_ORIGINAL_SCORE.v1','n':200,'counts':dict(counts),
         'pregrade_sha256':hashlib.sha256(sf.read_bytes()).hexdigest(),'rows':scores,
         'research_scope':'previously exposed published training split, not pristine external blind',
         'global_neural_exclusive_Q3':'OPEN','global_Q4_total10x':'OPEN'}
 out=pathlib.Path(a.out);out.parent.mkdir(exist_ok=True,parents=True);out.write_text(json.dumps(result,sort_keys=True)+'\n')
 print('FINAL_ORIGINAL200_TRANSFER',json.dumps(result['counts'],sort_keys=True),'sha256',
       hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
