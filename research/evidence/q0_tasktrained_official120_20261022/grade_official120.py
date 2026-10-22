#!/usr/bin/env python3
"""Independently grade unaltered actual trained local rule vs fixed no-learn color lookup on official public ARC2 EVAL120.
Exact source SHA and all120. Not hidden ARC prize official leaderboard; no frontier parity.
"""
import json,hashlib,pathlib,collections,argparse

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prediction',required=True);ap.add_argument('--official-dir',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 d=json.loads(pathlib.Path(a.prediction).read_text());assert d['n']==len(d['rows'])==120 and d['eval_labels_seen'] is False
 root=pathlib.Path(a.official_dir);fs=sorted(root.glob('*.json'));assert len(fs)==120 and {x.stem for x in fs}==set(d['rows'])
 status=collections.Counter();correct_any=[];correct_cv=[];color_correct=[];ledger={}
 for x in fs:
  id=x.stem;task=json.loads(x.read_text());raw=d['rows'][id];status[raw['status']]+=1
  truth=[v['output'] for v in task['test']]
  any_ok=raw.get('status')=='fit' and raw['prediction']==truth
  cv_ok=any_ok and bool(raw.get('cv_all',False))
  map_ok=bool(raw.get('mapping_fit')) and raw.get('baseline_color_lookup')==truth
  if any_ok:correct_any.append(id)
  if cv_ok:correct_cv.append(id)
  if map_ok:color_correct.append(id)
  ledger[id]={'status':raw['status'],'cv':raw.get('cv_all',False),'learned_correct':bool(any_ok),'learned_cv_correct':bool(cv_ok),'no_learn_color_correct':bool(map_ok)}
 o={'schema':'NEUMANN_Q0_ARC2_OFFICIAL_EVAL120_UNCHANGED_TASK_CONDITIONED_LEARNED_STRUCTURE_INDEPENDENT_SCORE.v1',
    'original_source_tree_sha':'8d04288aac3146b7c47d0b799c18bc9c0217d838',
    'prediction_sha256':hashlib.sha256(pathlib.Path(a.prediction).read_bytes()).hexdigest(),
    'eval_tasks':120,'actual_trained_model_exact':len(correct_any),'actual_trained_model_cv_gated_exact':len(correct_cv),
    'classical_color_lookup_exact':len(color_correct),'historical_fixed96_exact':0,
    'tree_fit_counts':dict(status),'exact_ids':sorted(correct_any),'cv_exact_ids':sorted(correct_cv),'no_learn_ids':sorted(color_correct),
    'learned_primitive_invention':False,'globally_independent_firstblind':False,
    'global_Q3':'OPEN','global_Q4_10x':'OPEN','frontier_parity':'OPEN',
    'all120':ledger}
 pathlib.Path(a.out).write_text(json.dumps(o,sort_keys=True,indent=2)+'\n')
 print('REAL_ACTUAL_LEARNED_LOCAL_RULE_ARC2_OFFICIAL_EVAL120',len(correct_any),len(correct_cv),'NO_TRAINING_CLASSICAL',len(color_correct),'FIT',status,flush=True)
if __name__=='__main__':main()
