#!/usr/bin/env python3
"""Same exact task-local ARC2 program synthesis + best-model selection + test prediction;
CPU matched actual end-to-end DSL solver, NOT whole NEUMANN/frontier model costs.
Never loads test outputs; no training or target answers in runner.
"""
import argparse,hashlib,json,pathlib,statistics,sys,time,importlib.util

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,str(pathlib.Path(path).resolve()))
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

ap=argparse.ArgumentParser()
for f in ['source','old','v1','v2','out']:ap.add_argument('--'+f,required=True)
ap.add_argument('--pairs',type=int,default=7)
x=ap.parse_args()
mods={'legacy':load('old',x.old),'shape_v1':load('cache',x.v1),'semantics_v2':load('semantics',x.v2)}
p=pathlib.Path(x.source)
fs=sorted(p.glob('*.json'),key=lambda f:hashlib.sha256(f.stem.encode()).hexdigest())
assert len(fs)==1000
subset=fs[:800:20];assert len(subset)==40
records=[]
for f in subset:
 d=json.loads(f.read_text())
 assert all('output' not in r for r in d['test'])
 records.append((f.stem,d))

def run(mod):
 preds=[];num_rules=0
 for id,task in records:
  rules=mod.task_rules(task)
  num_rules+=len(rules)
  best=min(rules,key=mod.complexity) if rules else None
  pred=mod.predict(task,best) if best else None
  preds.append({'id':id,'n':len(rules),'best':best,'prediction':pred})
 return preds,num_rules

paired=[]
for i in range(x.pairs):
 order=list(mods.items());order=order[i%3:]+order[:i%3]
 for name,mod in order:
  st=time.perf_counter();outputs,n=run(mod);elapsed=time.perf_counter()-st
  phash=hashlib.sha256(json.dumps(outputs,sort_keys=True).encode()).hexdigest()
  paired.append({'pair':i,'method':name,'wall_s':elapsed,'solution_count':sum(x['prediction'] is not None for x in outputs),'num_rules':n,'exact_output_hash':phash})
  print('FULL_SOLVER_PAIRED',i,name,round(elapsed,6),'SOLUTION',sum(x['prediction'] is not None for x in outputs),'SHA',phash,flush=True)
assert len(set(x['exact_output_hash'] for x in paired))==1
summary={name:dict(median_wall_s=statistics.median([r['wall_s'] for r in paired if r['method']==name]),
 n_repeats=x.pairs) for name in mods}
summary['full_dsl_inference_gain_old_to_v2']=summary['legacy']['median_wall_s']/summary['semantics_v2']['median_wall_s']
summary['full_dsl_inference_gain_v1_to_v2']=summary['shape_v1']['median_wall_s']/summary['semantics_v2']['median_wall_s']
out={'n_original_tasks':len(records),'same_solution_and_all_program_choices':True,'source':'public ARC2 training pinned, no hidden eval labels','training_cost_s':0,
 'scope':'complete zero-neural typed DSL proposer + best-rule selection + test input prediction (not entire NEUMANN with frontier model)',
 'summary':summary,'paired':paired,'model_full_compute_10x':'UNPROVEN'}
dest=pathlib.Path(x.out);dest.parent.mkdir(exist_ok=True,parents=True);dest.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print('COMPLETE_DSL_SOLVER_EXACT_PREDICTION_AND_COST',json.dumps(summary,sort_keys=True),flush=True)
