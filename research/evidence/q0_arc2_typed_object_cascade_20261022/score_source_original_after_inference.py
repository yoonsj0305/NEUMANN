#!/usr/bin/env python3
"""Strict independent postgrade original 200 labels, never run in model stage."""
import argparse,hashlib,json,pathlib,math

def main():
 ap=argparse.ArgumentParser()
 for arg in ('old-locked','new-locked','cascade-locked','truth-dir','out'):ap.add_argument('--'+arg,required=True)
 a=ap.parse_args()
 paths={n:pathlib.Path(getattr(a,n.replace('-','_'))) for n in ('old-locked','new-locked','cascade-locked')}
 old=json.loads(paths['old-locked'].read_text());new=json.loads(paths['new-locked'].read_text());cascade=json.loads(paths['cascade-locked'].read_text())
 assert old['n']==new['num']==cascade['n']==200
 indexed={x['id']:x for x in old['rows']}
 indexednew={x['id']:x for x in new['records']}
 assert len(indexed)==len(indexednew)==len(cascade['records'])==200
 rows=[]
 for c in cascade['records']:
  tid=c['id'];o=indexed[tid];n=indexednew[tid]
  target_task=json.loads((pathlib.Path(a.truth_dir)/(tid+'.json')).read_text())
  gold=[q['output'] for q in target_task['test']]
  tests={'old':o['new_guess'],'typed':n['pred'],'cascade':c['prediction']}
  rights={k:(g is not None and g==gold) for k,g in tests.items()}
  assert c['prediction']==(o['new_guess'] if o['old_coverage']+o['new_coverage']>0 else n['pred'])
  rows.append({'id':tid,'route':c['choice'],'old_covered':o['old_coverage']+o['new_coverage']>0,'new_covered':n['num_candidates']>0,**{k+'_exact':v for k,v in rights.items()}})
 result={'dataset':'arcprize/ARC-AGI-2 pinned f3283f727488ad98fe575ea6a5ac981e4a188e49 / public TRAIN800/200','scope':'POSTHOC on known 200; not firstblind / not frontier','originals_checked':200,'train_labels_used_to_choose_candidates':True,'test_outputs_used_at_inference':False,'neural_forward_count':0,'frozen_source_sha256':'e50877b81eb3af1a09ff35f5c4e9c5a6d49d284d5db72626addd3be866ef1037','first_grade_vintage':'original ARC2 compositional 200 receipt 9761c2e6..., tested prior to new method','old_prediction_hash':hashlib.sha256(paths['old-locked'].read_bytes()).hexdigest(),'typed_prediction_hash':hashlib.sha256(paths['new-locked'].read_bytes()).hexdigest(),'cascade_prediction_hash':hashlib.sha256(paths['cascade-locked'].read_bytes()).hexdigest(),'total':{k:sum(r[k+'_exact'] for r in rows) for k in ('old','typed','cascade')},'routes':cascade['route_counts'],'new_only_ids':[r['id'] for r in rows if r['typed_exact'] and not r['old_exact']],'old_only_ids':[r['id'] for r in rows if r['old_exact'] and not r['typed_exact']],'new_grammar_input_source_only':True,'learned_unique_discovery':'NOT_PROVEN','full_model_compute_10x':'NOT_PROVEN','generalized_frontier':'NOT_PROVEN','rows':rows}
 p=pathlib.Path(a.out);p.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
 assert result['total']=={'old':10,'typed':8,'cascade':11},result['total']
 assert result['new_only_ids']==['f25fbde4'],result['new_only_ids']
 print(json.dumps({k:result[k] for k in ('total','routes','new_only_ids','old_only_ids','old_prediction_hash','typed_prediction_hash','cascade_prediction_hash')},indent=2))
if __name__=='__main__':main()
