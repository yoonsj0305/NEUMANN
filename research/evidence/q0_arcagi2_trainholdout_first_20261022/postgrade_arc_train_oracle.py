#!/usr/bin/env python3
"""After frozen prediction receipt, separately evaluate ceiling of a fixed compositional grammar."""
import argparse,hashlib,json,pathlib
from arc_compositional_grammar import find_programs,predict

def main():
 p=argparse.ArgumentParser();p.add_argument('--predictions',required=True);p.add_argument('--training-root',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 f=pathlib.Path(a.predictions);payload=f.read_bytes();d=json.loads(payload)
 assert d['split']=='holdout' and d['n']==200
 root=pathlib.Path(a.training_root);ans={};candidate_count=0
 for row in d['decisions']:
  name=row['id'];t=json.loads((root/(name+'.json')).read_text());inp={'train':t['train'],'test':[{'input':z['input']} for z in t['test']]}
  if row['num_composition_candidates']==0:continue
  cand=find_programs(inp)
  assert len(cand)==row['num_composition_candidates']
  correct=any(predict(inp,x)==[z['output'] for z in t['test']] for x in cand)
  chosen=row['attempt']==[z['output'] for z in t['test']]
  ans[name]={'candidate_count':len(cand),'contains_correct_program':correct,'chosen_correct':chosen}
  candidate_count+=1
 result={'schema':'NEUMANN_ARC2_TRAIN200_POSTGRADED_FINITE_COMPOSER_CEILING.v1',
   'prediction_receipt_sha256':hashlib.sha256(payload).hexdigest(),
   'oracle_labels_only_used_after_prediction_receipt':True,
   'holdout_total':200,'demo_fitting_coverage':candidate_count,
   'oracle_true_program_count':sum(x['contains_correct_program'] for x in ans.values()),
   'selection_exact':sum(x['chosen_correct'] for x in ans.values()),
   'ranker_headroom':sum(x['contains_correct_program'] and not x['chosen_correct'] for x in ans.values()),
   'hard_fail_fit_but_wrong':[k for k,v in ans.items() if not v['contains_correct_program']],
   'oracle_program_task_details':ans,
   'interpretation':'An arbitrary trained reranker of exactly this frozen finite fitted candidate set cannot exceed this oracle exact solve count on this fixed cohort; does not imply inability of a new program generator to solve more.'}
 pathlib.Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print('EXACT_COMPOSITION_REPRESENTATION_CEILING',json.dumps({k:v for k,v in result.items() if k in ['holdout_total','demo_fitting_coverage','oracle_true_program_count','selection_exact','ranker_headroom']},sort_keys=True))
if __name__=='__main__':main()
