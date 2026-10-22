#!/usr/bin/env python3
"""Only invoked after holdout predictions are committed/hash archived."""
import argparse,collections,hashlib,json,pathlib

def main():
 p=argparse.ArgumentParser();p.add_argument('--predictions',required=True);p.add_argument('--training-root',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 fp=pathlib.Path(a.predictions);raw=fp.read_bytes();d=json.loads(raw)
 assert d['reg']['validation_n']==200 and d['split']=='holdout' and d['n']==200
 exact={'baseline':[],'composition':[],'new_comp_only':[]};covered={'baseline':0,'composition':0};ambiguous=0
 for rec in d['decisions']:
  t=json.loads((pathlib.Path(a.training_root)/(rec['id']+'.json')).read_text())
  def right(k):
   attempt=rec[k]
   return attempt is not None and len(attempt)==len(t['test']) and all(x==y['output'] for x,y in zip(attempt,t['test']))
  bo=right('baseline_attempt');co=right('attempt')
  if bo:exact['baseline'].append(rec['id'])
  if co:exact['composition'].append(rec['id'])
  if co and not bo:exact['new_comp_only'].append(rec['id'])
  if rec['num_simplest_dsl']:covered['baseline']+=1
  if rec['num_composition_candidates']:covered['composition']+=1
  if rec['num_composition_candidates']>1:ambiguous+=1
 assert len(d['decisions'])==200
 result={'schema':'NEUMANN_ARC2_INTERNAL_TRAIN_ONLY_200_FIRSTBLIND_GENERAL_COMPOSITION.v1',
  'source':'Official ARC-AGI-2 PUBLIC TRAINING 1000 split 800 dev / 200 holdout, NEVER official evaluation',
  'no_public_evaluation_answers_seen_or_used':True,'heldout_labels_absent_until_after_prediction_receipt':True,
  'prediction_archive_sha256':hashlib.sha256(raw).hexdigest(),'source_pin':d['reg']['pin'],
  'dev_ids_sha256':d['reg']['dev_id_sha256'],'holdout_ids_sha256':d['reg']['val_id_sha256'],
  'heldout':200,'coverage':covered,'exact_solves':{k:len(v) for k,v in exact.items()},
  'solved_ids':exact,'ambiguous_program_count':ambiguous,'composition_inference_seconds':d['wall_s'],
  'no_learned_only_operator':True,'global_frontier_parity':'NOT_PROVEN','global_Q3_new_operator':'NOT_PROVEN',
  'global_Q4_10x':'NOT_PROVEN','study_limitations':['train-derived internal split only, NOT official public eval first-run','no neural model in this new symbolic composer','fixed library + fitted color parameters, not arbitrary free program invention','strong symbolic or frontier LLM baselines not run']}
 out=pathlib.Path(a.out);out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'HOLDOUT':200,'EXACT':result['exact_solves'],'COVERAGE':covered,'wall_s':d['wall_s']},sort_keys=True))
if __name__=='__main__':main()
