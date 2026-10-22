#!/usr/bin/env python3
"""POSTGRADE exhaustive correct-program ORACLE only inside two FROZEN task-dependent grammars.
Must never be called by inference. Reads all source target answers, so no blindness.
"""
import argparse,pathlib,json,collections,time,hashlib
from arc_compositional_grammar import find_programs,predict as predict_old
from source_structural_v2 import synthesize_demos,predict as predict_new

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-dir',required=True);p.add_argument('--first-predictions',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 pre=pathlib.Path(a.first_predictions);payload=json.loads(pre.read_text());assert payload['total_tasks']==160 and payload['total_tests']==480 and payload['labels_accessible'] is False
 start=time.perf_counter();rows=[];s=collections.Counter()
 for prior in payload['rows']:
  f=pathlib.Path(a.source_dir)/(prior['id']+'.json');task=json.loads(f.read_text());truth=[t['output'] for t in task['test']]
  old_cand=find_programs(task);new_cand,_=synthesize_demos(task['train'])
  assert len(old_cand)==prior['old_demo_candidates'] and len(new_cand)==prior['new_demo_candidates'],prior['id']
  old_solutions=[str(candidate) for candidate in old_cand if predict_old(task,candidate)==truth]
  new_solutions=[c[1] for c in new_cand if predict_new(task['test'],c)==truth]
  old_solved=prior['old']==truth;new_solved=prior['new']==truth
  if old_solved:assert old_solutions
  if new_solved:assert new_solutions
  row={'id':prior['id'],'group':prior['group'],'old_all_fitting_candidates':len(old_cand),'new_all_fitting_candidates':len(new_cand),
       'old_oracle_all3':bool(old_solutions),'new_oracle_all3':bool(new_solutions),
       'old_selected_correct':old_solved,'new_selected_correct':new_solved,
       'new_oracle_winners':new_solutions,'old_oracle_winners':old_solutions}
  rows.append(row)
  for k in ['old_oracle_all3','new_oracle_all3','old_selected_correct','new_selected_correct']:
   s[k]+=int(row[k])
  s['new_only_oracle']+=int(bool(new_solutions) and not old_solutions)
  s['old_only_oracle']+=int(bool(old_solutions) and not new_solutions)
  s['oracle_union']+=int(bool(old_solutions or new_solutions))
  if len(rows)%40==0:print('POSTGRADE_EXHAUSTIVE_FROZEN_ORACLE',len(rows),flush=True)
 assert len(rows)==160
 ext=next(x for x in rows if x['id']=='ExtractObjects/ExtractObjects1')
 assert ext['old_all_fitting_candidates']==1 and ext['new_all_fitting_candidates']==1
 assert ext['new_oracle_all3'] and not ext['old_oracle_all3']
 result={'schema':'NEUMANN_Q0_POSTGRADE_FINITE_GRAMMAR_COMPARISON_ONLY.v1',
    'source_task_count':160,'source_test_count':480,'pregrade_sha256':hashlib.sha256(pre.read_bytes()).hexdigest(),
    'postgrade':True,'old_grammar_formally_exhausted_in_current_finite_implementation':True,
    'new_grammar_formally_exhausted_in_current_finite_implementation':True,
    'oracle_totals':dict(s),'extractobjects_structurally_new_certificate':ext,
    'rows':rows,'runtime_s':time.perf_counter()-start,
    'no_claims':'No global impossibility for all programs; no learned-operator novelty; no firstblind outcome for postgrade oracle; 1/160 incremental not statistically compelling.'}
 out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print('CONCEPTARC160_BOTH_FINITE_GRAMMARS_EXHAUSTED',dict(s),'unique_new_original',ext['id'],flush=True)
if __name__=='__main__':main()
