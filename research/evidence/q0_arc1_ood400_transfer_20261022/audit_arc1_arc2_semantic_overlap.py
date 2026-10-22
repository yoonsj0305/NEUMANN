#!/usr/bin/env python3
"""Original-source corpus-leakage audit, source-pinned: ARC1 public eval vs ARC2 train/eval.
Read-only deterministic canonicalization of actual task INPUT and OUTPUT arrays.
Training demonstrations are treated as an UNORDERED multiset; test array order retained.
Scientific scope: exact semantic task equality, NOT same-family or paraphrase leakage.
"""
import argparse,collections,hashlib,json,pathlib

def json_hash(obj):
 return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def canonical_task(data):
 def pair(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
 return json_hash({'train':sorted(map(pair,data['train'])),'test':list(map(pair,data['test']))})

def main():
 pa=argparse.ArgumentParser()
 for key in ('arc1_eval','arc2_train','arc2_eval','first_score','out'):pa.add_argument('--'+key.replace('_','-'),required=True)
 a=pa.parse_args()
 arc1=pathlib.Path(a.arc1_eval);arc2tr=pathlib.Path(a.arc2_train);arc2ev=pathlib.Path(a.arc2_eval)
 def files(path):return {x.stem:x for x in path.glob('*.json')}
 one=files(arc1);two=files(arc2tr);three=files(arc2ev)
 assert len(one)==400 and len(two)==1000 and len(three)==120
 scorebytes=pathlib.Path(a.first_score).read_bytes();score=json.loads(scorebytes)
 assert score['n']==400 and len(score['score'])==400
 assert score['pregade_artifact_sha256']=='98dba8c5432f437d296df95d0db2860f6354575313bfc18d5fb2bf713dd2ea47'
 prediction_results={x[0]:{'baseline_correct':bool(x[1]),'new_correct':bool(x[2])} for x in score['score']}; assert len(prediction_results)==400
 counters=collections.Counter();allrows=[]
 for taskid,p in sorted(one.items()):
  a_data=json.loads(p.read_text());sh=canonical_task(a_data)
  meta={'id':taskid,'arc1_semantic_sha256':sh}
  found=[]
  for split,dataset in [('arc2_training',two),('arc2_evaluation',three)]:
   if taskid in dataset:
    original=dataset[taskid];o=json.loads(original.read_text());same=canonical_task(o)==sh
    meta[split+'_same_id']=True;meta[split+'_semantically_equal']=same
    found.append(split)
    counters[split+'_id_overlap']+=1
    counters[split+'_semantically_equal']+=same
    if not same:
     meta[split+'_test_equal']=json_hash(a_data['test'])==json_hash(o['test'])
     meta[split+'_ordered_training_equal']=json_hash(a_data['train'])==json_hash(o['train'])
   else:meta[split+'_same_id']=False
  meta['disjoint_id']=not bool(found)
  for lab in ('baseline_correct','new_correct'):
   meta[lab]=prediction_results[taskid][lab]
  counters['all_tasks']+=1
  counters['disjoint_id']+=meta['disjoint_id']
  if meta['disjoint_id']:
   counters['disjoint_baseline_correct']+=meta['baseline_correct']
   counters['disjoint_new_correct']+=meta['new_correct']
  if found:
   counters['overlap_baseline_correct']+=meta['baseline_correct']
   counters['overlap_new_correct']+=meta['new_correct']
  allrows.append(meta)
 assert counters['all_tasks']==400
 result={'schema':'NEUMANN_Q0_ARC1_ARC2_CORPUS_CONTAMINATION_AUDIT.v1','arc1_commit':'399030444e0ab0cc8b4e199870fb20b863846f34','arc2_commit':'f3283f727488ad98fe575ea6a5ac981e4a188e49','first_pregrade_sha256':score['pregade_artifact_sha256'],'first_postgrade_sha256':hashlib.sha256(scorebytes).hexdigest(),'observed_counts':dict(counters),'semantic_exact_definition':'SHA256 canonical JSON with unordered sorted training pairs and ordered test pairs, both input and output grid arrays','classification':'ARC1 public eval cannot be considered independent OOD of ARC2 source-developed grammar when task IDs/semantics overlap','fully_different_task_family_guaranteed':False,'further_actions':'exclude even named overlaps before new prereg OOD; audit canonical task content & near duplicates across all partitions','rows':allrows}
 out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print('FROZEN_CROSS_CORPUS_CONTENT_LEAK_AUDIT',json.dumps(dict(counters),sort_keys=True),flush=True)
 print('EVIDENCE_SHA256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)

if __name__=='__main__':main()
