#!/usr/bin/env python3
"""ARC2 exact per-task program composition on public TRAIN split only.

No evaluation answer use, no learned primitive, no frontier victory claim.
The model learns only task-conditioned color mappings from demonstration pairs,
combines them with a finite generic geometry/object grammar and exact demo checks.
Each selected program emits predictions before the separate holdout grader.
"""
import argparse,collections,hashlib,json,pathlib,sys,time
import numpy as np
from arc_minimal_controller import PROGRAMS,run_program,arr,key,do_transform,components,bbox

OBJECT_OPS=('fill_global_bbox','outline_global_bbox','fill_component_bbox','outline_component_bbox','remove_isolated','reflect_lr_concat','reflect_ud_concat','diag_flip_pad')
NOMAP={}

def candidates_from_grammar():
 # 96 base operators, then 8*8 object composition operators.
 for i,p in enumerate(PROGRAMS):yield ('base',i,p)
 for trans in ('identity','flip_lr','flip_ud','rot90','rot180','rot270','transpose','anti_transpose'):
  for op in OBJECT_OPS:yield ('object',trans,op)

def run_object(x,trans,op):
 try:
  x=do_transform(arr(x),trans)
  if op in ('fill_global_bbox','outline_global_bbox'):
   m=x!=0;b=bbox(x,m)
   if b is None:return None
   q=x.copy();loc=np.argwhere(m);r0,c0=loc.min(axis=0);r1,c1=loc.max(axis=0)
   color=collections.Counter(int(z) for z in x[m]).most_common(1)[0][0]
   if op=='fill_global_bbox':q[r0:r1+1,c0:c1+1]=color
   else:
    q[r0,c0:c1+1]=color;q[r1,c0:c1+1]=color;q[r0:r1+1,c0]=color;q[r0:r1+1,c1]=color
   return q
  if op in ('fill_component_bbox','outline_component_bbox'):
   q=x.copy()
   for pts in components(x):
    ys=[v[0] for v in pts];xs=[v[1] for v in pts];r0=min(ys);r1=max(ys);c0=min(xs);c1=max(xs)
    col=int(x[pts[0][0],pts[0][1]])
    if op=='fill_component_bbox':q[r0:r1+1,c0:c1+1]=col
    else:
     q[r0,c0:c1+1]=col;q[r1,c0:c1+1]=col;q[r0:r1+1,c0]=col;q[r0:r1+1,c1]=col
   return q
  if op=='remove_isolated':
   q=x.copy()
   for pts in components(x):
    if len(pts)==1:q[pts[0][0],pts[0][1]]=0
   return q
  if op=='reflect_lr_concat':q=np.concatenate([x,np.fliplr(x)],axis=1)
  elif op=='reflect_ud_concat':q=np.concatenate([x,np.flipud(x)],axis=0)
  elif op=='diag_flip_pad':q=np.block([[x,np.fliplr(x)],[np.flipud(x),np.rot90(x,2)]])
  else:return None
  return q if 0<q.shape[0]<=30 and 0<q.shape[1]<=30 else None
 except (ValueError,IndexError):return None

def run_raw(grid,p):
 if p[0]=='base':return run_program(grid,p[2])
 return run_object(grid,p[1],p[2])

def fit_mapping(demos,p):
 lookup={}; valid=True
 for pair in demos:
  transformed=run_raw(pair['input'],p)
  if transformed is None:return None
  tgt=arr(pair['output']);
  if transformed.shape!=tgt.shape:return None
  for v in np.unique(transformed):
   m=transformed==v; mapped=np.unique(tgt[m])
   if len(mapped)!=1:return None
   k=int(v);a=int(mapped[0]);
   if k in lookup and lookup[k]!=a:return None
   lookup[k]=a
 return lookup

def apply_mapping(x,mapping):
 if x is None:return None
 return np.array([mapping.get(int(z),int(z)) for z in x.ravel()],dtype=np.int8).reshape(x.shape)

def find_programs(task):
 demos=task['train']; found=[]
 for p in candidates_from_grammar():
  exact=True
  for t in demos:
   y=run_raw(t['input'],p)
   if y is None or key(y)!=key(t['output']):exact=False;break
  if exact:found.append((p,None))
  mapping=fit_mapping(demos,p)
  if mapping is not None and any(k!=v for k,v in mapping.items()):
   # A learned program is admitted only when demo results are indeed identical
   if all(key(apply_mapping(run_raw(q['input'],p),mapping))==key(q['output']) for q in demos):
    found.append((p,mapping))
 return found

def program_complexity(c):
 p,cm=c
 return (1 if cm is not None else 0)+(sum(int(a!=b) for a,b in cm.items()) if cm else 0)+(0 if p[0]=='base' else 2)

def choose_program(programs):
 # Deliberately deterministic, favors known simpler exact program; no holdout labels.
 if not programs:return None
 return min(programs,key=lambda c:(program_complexity(c),str(c)))

def predict(task,c):
 if c is None:return None
 p,m=c;res=[]
 for x in task['test']:
  z=run_raw(x['input'],p)
  if m is not None:z=apply_mapping(z,m)
  if z is None:return None
  res.append(z.tolist())
 return res

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--data',required=True);parser.add_argument('--freeze',required=True);parser.add_argument('--out',required=True);parser.add_argument('--dev-only',action='store_true');a=parser.parse_args()
 reg=json.loads(pathlib.Path(a.freeze).read_text());root=pathlib.Path(a.data);allfiles=sorted(root.glob('*.json'))
 assert len(allfiles)==1000 and reg['dev_n']==800 and reg['validation_n']==200
 ordered=sorted(allfiles,key=lambda x:hashlib.sha256(x.stem.encode()).hexdigest());dev=ordered[:800];hold=ordered[800:]
 def digest(files):return hashlib.sha256(('\n'.join(x.stem for x in files)+'\n').encode()).hexdigest()
 assert digest(dev)==reg['dev_id_sha256'] and digest(hold)==reg['val_id_sha256']
 trials=dev if a.dev_only else hold
 start=time.perf_counter();records=[]
 for ix,f in enumerate(trials):
  full=json.loads(f.read_text())
  safe={'train':full['train'],'test':[{'input':x['input']} for x in full['test']]}
  allc=find_programs(safe);old=[]
  for p in PROGRAMS:
   if all((z:=run_program(q['input'],p)) is not None and key(z)==key(q['output']) for q in safe['train']):old.append(p)
  c=choose_program(allc)
  pred=predict(safe,c)
  old_best=old[0] if old else None
  old_pred=[] if old_best is not None else None
  if old_best is not None:
   for q in safe['test']:
    y=run_program(q['input'],old_best)
    if y is None:old_pred=None;break
    old_pred.append(y.tolist())
  # Note: oracle is computed strictly after predictions are saved in a separate process.
  records.append({'id':f.stem,'num_simplest_dsl':len(old),'num_composition_candidates':len(allc),
      'program':(str(c) if c is not None else None),'attempt':pred,
      'baseline_attempt':old_pred,
      'is_color_mapping':bool(c is not None and c[1] is not None)})
  if (ix+1)%100==0:print('SOURCE_ONLY_EVALUATED',ix+1,len(trials),flush=True)
 wall=time.perf_counter()-start
 out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
 payload={'schema':'NEUMANN_ARC2_GENERAL_COMPOSITION_TRAIN_HOLDOUT_PREGRADE.v1',
          'eval_labels_provided_to_solver':False,'reg':reg,'split':'dev' if a.dev_only else 'holdout',
          'n':len(trials),'wall_s':wall,'grammar_base_96':True,'grammar_object_ops':len(OBJECT_OPS)*8,
          'candidate_coverage':sum(x['num_composition_candidates']>0 for x in records),
          'baseline_coverage':sum(x['num_simplest_dsl']>0 for x in records),
          'decisions':records}
 p=json.dumps(payload,sort_keys=True,separators=(',',':')).encode();out.write_bytes(p)
 print('PREDICTION_FIRST_SHA256',hashlib.sha256(p).hexdigest(),'COUNT',len(trials),'BASE_COVER',payload['baseline_coverage'],'EXT_COVER',payload['candidate_coverage'],'WALL_S',wall,flush=True)
if __name__=='__main__':main()
