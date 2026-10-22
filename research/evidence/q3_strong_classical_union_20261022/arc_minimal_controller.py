#!/usr/bin/env python3
"""NEUMANN Q0 frontier gap: deterministic program induction and learned selection.

Evaluation security: model only receives stripped test input; no evaluator answer
until independent grading after predictions are archived. Torch learner is trained
only on official TRAIN task hidden training-set test labels. Programs are finite,
not new primitives invented by the network. All exact demo-fitting candidates
within a frozen library are checked for representation ceiling on evaluation.
"""
import argparse, collections, hashlib, json, math, os, pathlib, random, statistics, sys, time
import numpy as np

COMMIT='f3283f727488ad98fe575ea6a5ac981e4a188e49'
TRANSFORMS=['identity','flip_lr','flip_ud','rot90','rot180','rot270','transpose','anti_transpose']
POST=['identity','crop_0','crop_major','crop_largest','crop_smallest','crop_border','up2','up3','tile2','down2','down3','unique_1x1']
PROGRAMS=[(a,b) for a in TRANSFORMS for b in POST]
# fixed program universe: 96 programs, NO parameters or per-task arbitrary synthesis.
assert len(PROGRAMS)==96

def arr(x):
 a=np.asarray(x,dtype=np.int8)
 if a.ndim!=2 or not (1<=a.shape[0]<=30 and 1<=a.shape[1]<=30) or np.any(a<0) or np.any(a>9): raise ValueError('invalid ARC grid')
 return a

def key(x):return tuple(map(tuple,np.asarray(x).tolist()))

def bbox(x,mask):
 coords=np.argwhere(mask)
 if len(coords)==0:return None
 r0,c0=coords.min(axis=0);r1,c1=coords.max(axis=0)
 return x[r0:r1+1,c0:c1+1]

def components(x,background=0):
 m=x!=background; h,w=x.shape;seen=np.zeros((h,w),dtype=bool);pieces=[]
 for i in range(h):
  for j in range(w):
   if not m[i,j] or seen[i,j]:continue
   q=[(i,j)];seen[i,j]=1;pts=[]
   while q:
    a,b=q.pop();pts.append((a,b))
    for aa,bb in ((a+1,b),(a-1,b),(a,b+1),(a,b-1)):
     if 0<=aa<h and 0<=bb<w and m[aa,bb] and not seen[aa,bb]:seen[aa,bb]=True;q.append((aa,bb))
   pieces.append(pts)
 return pieces

def do_transform(x,name):
 if name=='identity':return x
 if name=='flip_lr':return np.fliplr(x)
 if name=='flip_ud':return np.flipud(x)
 if name=='rot90':return np.rot90(x,1)
 if name=='rot180':return np.rot90(x,2)
 if name=='rot270':return np.rot90(x,3)
 if name=='transpose':return x.T
 if name=='anti_transpose':return np.flipud(np.fliplr(x.T))
 raise ValueError(name)

def do_post(x,name):
 if name=='identity':return x
 if name=='crop_0':return bbox(x,x!=0)
 if name=='crop_major':
  labs,counts=np.unique(x,return_counts=True);bg=int(labs[np.argmax(counts)]);return bbox(x,x!=bg)
 if name in ('crop_largest','crop_smallest'):
  comps=components(x);comps=sorted(comps,key=lambda z:(len(z),min(z)),reverse=name=='crop_largest')
  if not comps:return None
  pts=comps[0];r=[p[0] for p in pts];c=[p[1] for p in pts];return x[min(r):max(r)+1,min(c):max(c)+1]
 if name=='crop_border':return x[1:-1,1:-1] if min(x.shape)>2 else None
 if name=='up2':return np.repeat(np.repeat(x,2,axis=0),2,axis=1)
 if name=='up3':return np.repeat(np.repeat(x,3,axis=0),3,axis=1)
 if name=='tile2':return np.tile(x,(2,2))
 if name=='down2':
  if min(x.shape)<2 or x.shape[0]%2 or x.shape[1]%2:return None
  return x[::2,::2]
 if name=='down3':
  if min(x.shape)<3 or x.shape[0]%3 or x.shape[1]%3:return None
  return x[::3,::3]
 if name=='unique_1x1':
  values,counts=np.unique(x,return_counts=True);order=sorted(zip(counts,values));return np.array([[order[0][1]]],dtype=np.int8)
 raise ValueError(name)

def run_program(grid,program):
 try:
  x=do_transform(arr(grid),program[0]);x=do_post(x,program[1]);
  if x is None or not (1<=x.shape[0]<=30 and 1<=x.shape[1]<=30):return None
  return x
 except (ValueError,TypeError,IndexError):return None

def task_candidates(task):
 # Never reads test OUTPUT. Exact program must fit EVERY supplied demo.
 out=[]
 for i,p in enumerate(PROGRAMS):
  good=True
  for pair in task['train']:
   x=run_program(pair['input'],p)
   if x is None or key(x)!=key(pair['output']):good=False;break
  if good:out.append(i)
 return out

def features(task):
 demos=task['train'];vals=[]
 for q in demos:
  a=arr(q['input']);b=arr(q['output']);sv,sc=np.unique(a,return_counts=True)
  ratio=float((a!=0).mean());bg=int(sv[np.argmax(sc)])
  vals.append([math.log1p(a.shape[0])/4,math.log1p(a.shape[1])/4,
   math.log1p(b.shape[0])/4,math.log1p(b.shape[1])/4,
   b.shape[0]/a.shape[0]/4,b.shape[1]/a.shape[1]/4,
   len(sv)/10,len(np.unique(b))/10,ratio,float((a!=bg).mean()),
   float(a.shape==b.shape if False else a.shape==b.shape),
   float(np.all(a==b)) if a.shape==b.shape else 0.0,
   float(a.shape[0]==a.shape[1]),float(b.shape[0]==b.shape[1]),
   float(np.count_nonzero(a==0))/a.size,float(np.count_nonzero(b==0))/b.size])
 v=np.mean(vals,axis=0).tolist()
 return np.array(v+[min(len(demos),6)/6],dtype=np.float32)

def op_feats(i):
 a,b=PROGRAMS[i];v=np.zeros(len(TRANSFORMS)+len(POST),dtype=np.float32)
 v[TRANSFORMS.index(a)]=1;v[len(TRANSFORMS)+POST.index(b)]=1
 return v

OP_FEATURES=np.stack([op_feats(i) for i in range(len(PROGRAMS))])

def learner_dataset(records):
 X=[];Y=[];count=0
 for task in records:
  cand=task_candidates(task)
  if not cand:continue
  # Train supervision uses TRAINING split reference labels only, never eval.
  target=[pair['output'] for pair in task['test']]
  tc=features(task)
  for i in cand:
   positive=all((z:=run_program(pair['input'],PROGRAMS[i])) is not None and key(z)==key(out)
                 for pair,out in zip(task['test'],target))
   X.append(np.concatenate((tc,OP_FEATURES[i])));Y.append(int(positive))
  count+=1
 if not X:raise RuntimeError('training has no demo-fitting programs')
 return np.stack(X),np.asarray(Y,dtype=np.float32),count

def train_policy(train_records,seed=20261022):
 import torch
 torch.set_num_threads(1);torch.manual_seed(seed);np.random.seed(seed);random.seed(seed)
 X,Y,n=learner_dataset(train_records)
 # Input length=17 + 20; small model 37x48x1, CPU only.
 model=torch.nn.Sequential(torch.nn.Linear(X.shape[1],48),torch.nn.ReLU(),torch.nn.Linear(48,1))
 tx=torch.from_numpy(X);ty=torch.from_numpy(Y)
 pos=float(Y.sum());neg=float(len(Y)-pos)
 if pos<1:raise RuntimeError('NO_TRUE_OPERATOR_IN_TRAINING: cannot fit useful selector')
 opt=torch.optim.AdamW(model.parameters(),lr=0.004,weight_decay=0.001)
 loss=torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor(min(20,neg/max(pos,1))))
 t=time.perf_counter()
 for epoch in range(65):
  opt.zero_grad(set_to_none=True);pred=model(tx).squeeze(1);l=loss(pred,ty);l.backward();opt.step()
 wall=time.perf_counter()-t
 model.eval()
 # Separate non-neural strongest pretraining-labeled count prior.
 counts={i:[0,0] for i in range(len(PROGRAMS))}
 for x,y in zip(X,Y):
  i=int(np.argmax(x[17:25]))*len(POST)+int(np.argmax(x[25:]))
  counts[i][0]+=int(y);counts[i][1]+=1
 prior={i:(pos+1)/(total+2) for i,(pos,total) in counts.items()}
 return model,prior,{'train_s':wall,'n_demo_fit_training_tasks':n,'candidate_training_samples':len(Y),'positive_train_candidates':int(Y.sum()),'n_parameters':sum(p.numel() for p in model.parameters()),'epochs':65}

def rank(task,cand,method,model,prior):
 if method=='mdl':return sorted(cand)
 if method=='frequency':return sorted(cand,key=lambda i:(-prior[i],i))
 if method=='hybrid':
  if len(cand)==1:return cand
  method='neural'
 if method=='neural':
  import torch
  with torch.no_grad():
   base=features(task);xs=np.stack([np.concatenate((base,OP_FEATURES[i])) for i in cand]);scores=model(torch.from_numpy(xs)).squeeze(1).numpy()
  return [i for _,i in sorted(zip(scores,cand),key=lambda p:(-float(p[0]),p[1]))]
 raise ValueError(method)

def infer_task(task,method,model,prior):
 cand=task_candidates(task)
 if not cand:return {'candidates':0,'attempt':None,'op':None,'extra_ops':[]}
 ranked=rank(task,cand,method,model,prior)
 preds=[]
 for pair in task['test']:
  o=run_program(pair['input'],PROGRAMS[ranked[0]])
  preds.append(o.tolist() if o is not None else None)
 return {'candidates':len(cand),'attempt':preds,'op':ranked[0], 'extra_ops':ranked[1:]}

def canon_task(t):return {'train':t['train'],'test':[{'input':x['input']} for x in t['test']]}

def valid_prediction(p,t):return p is not None and len(p)==len(t['test']) and all(x is not None and x==y['output'] for x,y in zip(p,t['test']))

def freeze_csv_manifest(path,folder,allfiles):
 rows=json.loads(pathlib.Path(path).read_text())
 assert rows['repository_commit']==COMMIT and rows['training_count']==1000 and rows['evaluation_count']==120
 assert len(allfiles)==rows['training_count']+rows['evaluation_count']
 # Must match sha256 metadata hash derived from exact ordered filename list, independent of grid body.
 ids=sorted(str(p.relative_to(folder)) for p in allfiles)
 h=hashlib.sha256(('\n'.join(ids)+'\n').encode()).hexdigest()
 assert h==rows['filename_manifest_sha256'],(h,rows['filename_manifest_sha256'])
 return h

def cmd_run(args):
 root=pathlib.Path(args.root);train_dir=root/'data/training';eval_dir=root/'data/evaluation'
 allpaths=list(train_dir.glob('*.json'))+list(eval_dir.glob('*.json'))
 frozen_hash=freeze_csv_manifest(args.freeze,root,allpaths)
 tr=[json.loads(x.read_text()) for x in sorted(train_dir.glob('*.json'))]
 assert len(tr)==1000
 t=time.perf_counter();model,prior,fit=train_policy(tr);train_wall=time.perf_counter()-t
 # Lock predictions before any test answers get decoded.
 target_files=sorted(eval_dir.glob('*.json'))
 pred={m:{} for m in ('mdl','frequency','neural','hybrid')};cand_ceiling=[]
 t=time.perf_counter()
 for fp in target_files:
  public=json.loads(fp.read_text());inp=canon_task(public)
  for m in pred:pred[m][fp.stem]=infer_task(inp,m,model,prior)
 # Inference outcomes are saved PRIOR to grading. Test outputs were stripped.
 io_wall=time.perf_counter()-t
 out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
 prediction={'schema':'NEUMANN_ARC2_Q0_PREDICTIONS_PRE_GRADE.v1','repository_commit':COMMIT,
    'manifest_sha256':frozen_hash,'train_only_fit':fit,'train_wall_total_s':train_wall,
    'evaluation_wall_total_s':io_wall,'rankers':pred,'evaluation_size':len(target_files),
    'eval_test_labels_passed_to_inference':0,'programs':PROGRAMS}
 payload=json.dumps(prediction,sort_keys=True,separators=(',',':')).encode();pre_hash=hashlib.sha256(payload).hexdigest()
 (out/'PREDICTIONS_BEFORE_GRADE.json').write_bytes(payload)
 if args.predictions_only:
  print(json.dumps({'prediction_sha256':pre_hash,'train_wall_s':train_wall,'inference_wall_s':io_wall,'eval_label_fields_received':0,'candidate_library':len(PROGRAMS),'evaluated':len(target_files)},sort_keys=True),flush=True)
  return
 # Explicitly open ground truth after archived predictions exist.
 truth={x.stem:json.loads(x.read_text()) for x in target_files}
 assert len(truth)==120
 metrics={}
 for name,preds in pred.items():
  good=[];bad=[];covered=[]
  for tid,res in preds.items():
   (good if valid_prediction(res['attempt'],truth[tid]) else bad).append(tid)
   if res['candidates']>0:covered.append(tid)
  metrics[name]={'solved':len(good),'total':len(preds),'solved_ids':good,'unsolved_ids':bad,'demo_fit_coverage':len(covered)}
 # Complete finite DSL ORACLE ceiling: full equal-rights allowed program list,
 # only inference demo-fit candidates; does not enter choice process.
 t=time.perf_counter()
 for tid,tgt in truth.items():
  c=pred['mdl'][tid]['extra_ops'].copy()
  idx=pred['mdl'][tid]['op']
  if idx is not None:c.insert(0,idx)
  success=any(all((p:=run_program(q['input'],PROGRAMS[i])) is not None and key(p)==key(q['output']) for q in tgt['test']) for i in c)
  if success:cand_ceiling.append(tid)
 oracle_wall=time.perf_counter()-t
 for v in metrics.values():
  assert v['solved']<=len(cand_ceiling)
 compiled={'schema':'NEUMANN_ARC2_Q0_FIRST_REAL_FRONTIER_GAP.v1','pin':COMMIT,
  'predictions_sha256':pre_hash,'train_only_fit':fit,'train_time_s':train_wall,
  'evaluation_inference_time_s':io_wall,'oracle_grading_time_s':oracle_wall,
  'test_output_leakage':False,'eval_tasks':120,'training_tasks':1000,
  'finite_primitive_programs':len(PROGRAMS),'results':metrics,
  'upper_ceiling_any_program_fits_demos_and_test':len(cand_ceiling),
  'oracle_ceiling_solved_ids':cand_ceiling,
  'strongest_control':'EXHAUSTIVE_MDL_AND_ALL_GRAMMAR_ORACLE_PLUS_FREQUENCY_PRIOR',
  'frontier_parity':'NOT_ESTABLISHED','learning_new_primitive':'NOT_ESTABLISHED',
  'tenfold_end_to_end_computation':'NOT_ESTABLISHED',
  'scientific_gate':'FAIL_UNLESS_DATA_PROVES_COMPETITIVE_FRONTIER_ACCURACY_AND_COST'}
 (out/'OFFICIAL_FIRST_EVAL_RESULT.json').write_text(json.dumps(compiled,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'all':{m:v['solved'] for m,v in metrics.items()},'ceiling':len(cand_ceiling),
   'train_s':train_wall,'eval_s':io_wall,'sample_size':120,'registered_manifest_sha256':frozen_hash},sort_keys=True),flush=True)


def cmd_selftest(_):
 xs=[[[1,2],[3,4]],[[0,0,0],[0,1,0],[0,0,0]]]
 for x in xs:
  for op in PROGRAMS:
   r=run_program(x,op)
   assert r is None or (1<=len(r)<=30 and 1<=len(r[0])<=30)
 task={'train':[{'input':[[1,2],[3,4]],'output':[[2,4],[1,3]]}], 'test':[{'input':[[5,6],[7,8]]}]}
 assert 3*len(POST) in task_candidates(task) # rot90
 assert infer_task(task,'mdl',None,None)['candidates']>=1
 assert all('output' not in t for t in canon_task({'train':task['train'],'test':[{'input':[[1]],'output':[[2]]} ]})['test'])
 print('SELFTEST_PASS_DSL_NO_LABEL_INFERENCE',len(PROGRAMS))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--selftest',action='store_true');parser.add_argument('--root');parser.add_argument('--freeze');parser.add_argument('--out');parser.add_argument('--predictions-only',action='store_true')
 args=parser.parse_args()
 if args.selftest:cmd_selftest(args)
 else:
  for k in ('root','freeze','out'):
   if getattr(args,k) is None:parser.error('--'+k+' required')
  cmd_run(args)
