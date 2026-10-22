#!/usr/bin/env python3
"""Run already-frozen symbolic ARC2 composer on official PUBLIC EVAL 120 with inputs only.
This is POSTHOC transfer, since a different frozen 96-DSL model has already scored this corpus.
No output labels or task-specific fitting from eval test answers.
"""
import argparse,hashlib,json,pathlib,time
from arc_compositional_grammar import find_programs,choose_program,predict
from arc_minimal_controller import PROGRAMS,run_program,key

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--data',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 root=pathlib.Path(a.data);paths=sorted(root.glob('*.json'))
 assert len(paths)==120,('expected complete 120',len(paths))
 t0=time.perf_counter();rows=[]
 for f in paths:
  raw=json.loads(f.read_text());assert all('output' not in t for t in raw['test'])
  valid=find_programs(raw)
  best=choose_program(valid)
  baseline=[]
  for op in PROGRAMS:
   if all((z:=run_program(item['input'],op)) is not None and key(z)==key(item['output']) for item in raw['train']): baseline.append(op)
  old_pred=None
  if baseline:
   old_pred=[]
   for q in raw['test']:
    z=run_program(q['input'],baseline[0]);
    if z is None:old_pred=None;break
    old_pred.append(z.tolist())
  rows.append({'id':f.stem,'num_fitting_programs':len(valid),'num_baseline_programs':len(baseline),
               'prediction':predict(raw,best),'baseline_prediction':old_pred,
               'source_algorithm':'FROZEN_SOURCE_ONLY_COMPOSITION_POSTHOC_TRANSFER_NO_EVAL_LABELS'})
 report={'schema':'NEUMANN_ARC2_FROZEN_COMPOSITION_EVAL120_POSTHOC_PREGRADE.v1',
         'fixed_official_commit':'f3283f727488ad98fe575ea6a5ac981e4a188e49',
         'evaluation_total':120,'output_labels_provided_to_inference':False,
         'training_model_calls':0,'public_evaluation_historically_opened_by_prior_fixed96_run':True,
         'num_fitting_program_tasks':sum(r['num_fitting_programs']>0 for r in rows),
         'num_baseline_fitting_tasks':sum(r['num_baseline_programs']>0 for r in rows),
         'wall_s':time.perf_counter()-t0,'rows':rows}
 target=pathlib.Path(a.out);target.write_text(json.dumps(report,sort_keys=True,separators=(',',':')))
 print('POSTHOC_PREDICTIONS_BEFORE_GRADE',len(rows),'demo_fits',report['num_fitting_program_tasks'],
       'base_demo_fits',report['num_baseline_fitting_tasks'],'wall',report['wall_s'],
       'sha256',hashlib.sha256(target.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
