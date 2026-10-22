#!/usr/bin/env python3
"""DEVELOPMENT-ONLY bounded syntactic composition search. Cannot claim learned novelty.
Scans frozen first 64 SHA-ordered DEV800 ARC-AGI-2 TRAIN original problems, never official EVAL.
"""
import argparse,collections,hashlib,json,pathlib,time,itertools
import numpy as np
from arc_compositional_grammar import candidates_from_grammar,run_raw,fit_mapping,apply_mapping,find_programs,predict,choose_program
from arc_minimal_controller import arr,key
OPS=list(candidates_from_grammar())

def fit_from_arrays(xs,ys):
 mapping={}
 for x,y in zip(xs,ys):
  if x is None or x.shape!=y.shape:return None
  for v in np.unique(x):
   idx=x==v; vals=np.unique(y[idx]);
   if len(vals)!=1:return None
   v=int(v); w=int(vals[0]);
   if v in mapping and mapping[v]!=w:return None
   mapping[v]=w
 return mapping

def discover(task, budget=25000):
 xs=[q['input'] for q in task['train']];ys=[arr(q['output']) for q in task['train']];train_inputs=tuple(xs)
 # Preserve original semantics: no labels exposed from test.
 stage1=[];unique_seen=set();evalcalls=0
 for p in OPS:
  temp=[run_raw(x,p) for x in xs];evalcalls+=len(xs)
  if any(z is None for z in temp):continue
  sig=tuple(key(x) for x in temp)
  if sig in unique_seen:continue
  unique_seen.add(sig);stage1.append((p,temp))
 # Dedup entire input -> intermediate semantics; only if stage1 has no semantic target solution.
 valid=[];p2attempts=0
 for p1,temp in stage1:
  for p2 in OPS:
   if p2attempts>=budget:break
   p2attempts+=1
   z0=run_raw(temp[0],p2);evalcalls+=1
   if z0 is None or z0.shape!=ys[0].shape:continue
   # First demo must permit a FUNCTIONAL color mapping; necessary condition.
   m=fit_from_arrays([z0],[ys[0]])
   if m is None:continue
   outs=[z0]
   for x in temp[1:]:
    z=run_raw(x,p2);evalcalls+=1
    if z is None:break
    outs.append(z)
   if len(outs)!=len(temp):continue
   m=fit_from_arrays(outs,ys)
   if m is None:continue
   if all(key(apply_mapping(z,m))==key(y) for z,y in zip(outs,ys)):
    # Model selection uses only demos and deterministic description length.
    complexity=5+sum(int(a!=b) for a,b in m.items())+(2 if p1[0]=='object' else 0)+(2 if p2[0]=='object' else 0)
    valid.append((complexity,str(p1),str(p2),p1,p2,m))
  if p2attempts>=budget:break
 if not valid:return None,{'stage1_unique':len(stage1),'attempts':p2attempts,'evalcalls':evalcalls,'solutions':0}
 _,_,_,p1,p2,m=min(valid,key=lambda z:z[:3]);pred=[]
 for item in task['test']:
  z=run_raw(item['input'],p1);z=run_raw(z,p2) if z is not None else None
  z=apply_mapping(z,m);pred.append(z.tolist() if z is not None else None)
 return pred,{'stage1_unique':len(stage1),'attempts':p2attempts,'evalcalls':evalcalls,'solutions':len(valid),'p1':str(p1),'p2':str(p2)}

def main():
 p=argparse.ArgumentParser();p.add_argument('--training-dir',required=True);p.add_argument('--n',type=int,default=32);p.add_argument('--out',required=True);a=p.parse_args()
 files=sorted(pathlib.Path(a.training_dir).glob('*.json'),key=lambda f:hashlib.sha256(f.stem.encode()).hexdigest());assert len(files)==1000
 files=files[:a.n];report=[];begin=time.perf_counter()
 for idx,f in enumerate(files):
  task=json.loads(f.read_text());b=find_programs({'train':task['train'],'test':[{'input':x['input']} for x in task['test']]})
  best=choose_program(b);baseline=predict(task,best) if best else None
  basecorrect=bool(baseline and baseline==[q['output'] for q in task['test']]);onecorrect=bool(b)
  if b: # Never do expensive nested search when an exact demo-consistent single composition already exists.
   report.append({'id':f.stem,'coverage_single':True,'correct_single':basecorrect,'coverage_two':False,'correct_two':False,'skipped':'cheaper valid one-step'})
  else:
   guess,detail=discover({'train':task['train'],'test':[{'input':x['input']} for x in task['test']]})
   correct=bool(guess and guess==[q['output'] for q in task['test']]);report.append({'id':f.stem,'coverage_single':False,'correct_single':False,'coverage_two':bool(guess),'correct_two':correct,'details':detail})
  if (idx+1)%8==0:print('DEV_PROGRESS',idx+1,'new_correct',sum(z['correct_two'] for z in report),'wall',time.perf_counter()-begin,flush=True)
 result={'scope':'DEVELOPMENT_ONLY_NOT_FIRSTBLIND_NO_EVAL','dev_sample_sha256':hashlib.sha256(('\n'.join(f.stem for f in files)+'\n').encode()).hexdigest(),
 'n':a.n,'baseline_correct':sum(z['correct_single'] for z in report),'extra_chain_correct':sum(z['correct_two'] for z in report),
 'single_covered':sum(z['coverage_single'] for z in report),'two_extra_covered':sum(z['coverage_two'] for z in report),
 'duration_s':time.perf_counter()-begin,'rows':report}
 pathlib.Path(a.out).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
 print('DEV_END',result['n'],result['baseline_correct'],result['extra_chain_correct'],result['duration_s'],flush=True)
if __name__=='__main__':main()
