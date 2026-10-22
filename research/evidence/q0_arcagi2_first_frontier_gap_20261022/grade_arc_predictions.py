#!/usr/bin/env python3
"""Separate frozen ARC-AGI-2 public evaluation grader.
Never imported by inference. Reads pre-archived SHA verified predictions and
canonical original public eval truth only after inference has terminated.
"""
import argparse,hashlib,json,pathlib,statistics,sys
from arc_minimal_controller import PROGRAMS,run_program,key

def main():
 p=argparse.ArgumentParser();p.add_argument('--predictions',required=True);p.add_argument('--eval-root',required=True);p.add_argument('--out',required=True);args=p.parse_args()
 path=pathlib.Path(args.predictions);b=path.read_bytes();blob=hashlib.sha256(b).hexdigest();d=json.loads(b)
 assert d['eval_test_labels_passed_to_inference']==0 and d['evaluation_size']==120
 assert len(d['programs'])==len(PROGRAMS)==96 and list(map(tuple,d['programs']))==PROGRAMS
 truth={x.stem:json.loads(x.read_text()) for x in sorted(pathlib.Path(args.eval_root).glob('*.json'))}
 assert len(truth)==120 and all(len(x['test'])>=1 and all('output' in z for z in x['test']) for x in truth.values())
 metrics={};ceiling=[]
 for label,sol in d['rankers'].items():
  good=[];miss=[];covered=[];multi=[]
  assert set(sol)==set(truth)
  for task_id,x in sol.items():
   correct=x['attempt'] is not None and len(x['attempt'])==len(truth[task_id]['test']) and all(
    v is not None and v==t['output'] for v,t in zip(x['attempt'],truth[task_id]['test']))
   (good if correct else miss).append(task_id)
   if x['candidates']>0:covered.append(task_id)
   if x['candidates']>1:multi.append(task_id)
  metrics[label]={'solved':len(good),'solved_ids':good,'unsolved_ids':miss,'candidate_coverage':len(covered),'ambiguity_count':len(multi)}
 for task_id,t in truth.items():
  x=d['rankers']['mdl'][task_id];ops=[x['op']]+x['extra_ops'] if x['op'] is not None else []
  if any(all((z:=run_program(q['input'],PROGRAMS[idx])) is not None and key(z)==key(q['output']) for q in t['test']) for idx in ops):ceiling.append(task_id)
 assert all(z['solved']<=len(ceiling) for z in metrics.values())
 file={'schema':'NEUMANN_ARC2_OFFICIAL_FIRST_FROZEN_Q0_GAP.v1','pinned_repository_sha':d['repository_commit'],
       'filename_manifest_sha256':d['manifest_sha256'],'predictions_sha256':blob,
       'n_public_training':1000,'n_public_eval':120,
       'first_trial':True,'separate_original_grading':True,'inference_received_eval_output':False,
       'program_dsl_size':len(PROGRAMS),'train_time_s':d['train_wall_total_s'],
       'inference_wall_s':d['evaluation_wall_total_s'],'train_statistics':d['train_only_fit'],
       'results':metrics,'oracle_any_demo_fitting_program_solved':len(ceiling),
       'oracle_solved_ids':ceiling,'important_limitations':[
        'The oracle is a representation ceiling for this EXACT finite hand-designed DSL only.',
        'Neural ranks fixed human-supplied transforms; it does not invent a new operator or demonstrate frontier-level performance.',
        'The public ARC-AGI-2 eval is NOT the private competition benchmark; this is a single frozen test, no retune after answer inspection.',
        'Training uses all public training task answers; evaluation answers are isolated until prediction output is archived.',
        'No LLM/paid API direct frontier-model baseline run or tokens/joules available.',
        'Setup costs, neural training, inference and oracle scoring listed separately, do not conflate with 10x end-to-end reduction.',
       ],'global_neumann_frontier_parity':'OPEN','neural_only_new_structure':'OPEN','global_Q4_10x':'OPEN'}
 out=pathlib.Path(args.out);out.write_text(json.dumps(file,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'status':'OFFICIAL_FROZEN_Q0_BENCHMARK_COMPLETE','solved':{k:v['solved'] for k,v in metrics.items()},'oracle_ceiling':len(ceiling),'n_eval':120,'train_wall_s':d['train_wall_total_s']},sort_keys=True),flush=True)
if __name__=='__main__':main()
if __name__=='__main__':main()
