#!/usr/bin/env python3
"""Q3 DEVELOPMENT ONLY: train source-local continuous latent conservation relation.
No hand-authored source invariants, no gold labels. Strong classical nullspace
is a necessary control and this path makes no new-primitive or baseline win claim.
"""
import sys, pathlib, re, random, time, json, hashlib, math, itertools, argparse, traceback
import numpy as np
import torch
import sympy as sp
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent/'q3_source_houdini_sha12_20261022'))
import classical_houdini as p
def parse_answer(raw, vars):
 if not raw or raw[0]!='sat':return None
 s=' '.join(raw[1:]); out=[]
 for v in vars:
  q=re.search(r'\('+re.escape(v)+r'\s+(\(-\s*\d+\s*\)|-?\d+)\)',s)
  if not q:return None
  text=q.group(1);out.append(-int(re.search(r'\d+',text).group()) if text.startswith('(-') else int(text))
 return out

def query(head,pred,names,rng,kind,count=32):
 vars=names+([x+'!' for x in names] if kind=='trans' else [])
 rows=[]
 bound=' '.join(f'(assert (and (>= {v} (- 20)) (<= {v} 20)))' for v in vars)
 for i in range(count*6):
  pick=names[i%len(names)];val=rng.randint(-10,10)
  pin=f'(assert (= {pick} {val}))' if i%4 else ''
  block='\n'.join('(assert (not (and '+' '.join(f'(= {v} {num if num>=0 else f"(- {-num})"})' for v,num in zip(vars,row))+')))' for row in rows[-12:])
  script=head+'\n'+bound+'\n(assert '+pred+')\n'+pin+'\n'+block+'\n(check-sat)\n(get-value ('+' '.join(vars)+'))'
  preflight=p.z.run(script.split('\n(get-value (')[0]+'\n')
  if preflight != ['sat']:
   continue
  ans=p.z.run(script)
  xx=parse_answer(ans,vars)
  if xx is not None and xx not in rows:rows.append(xx)
  if len(rows)>=count:break
 return rows

def expr(coeff,names):
 parts=[]
 for c,n in zip(coeff,names):
  if c==1:parts.append(n)
  elif c==-1:parts.append('(- '+n+')')
  elif c>1:parts.append(f'(* {c} {n})')
  elif c< -1:parts.append(f'(* (- {-c}) {n})')
 return p.plus(parts)

def quantize(w):
 a=w.detach().numpy();a=a/(max(abs(a))+1e-10)
 from fractions import Fraction
 # Only round one learned vector to a small integer AST. Do not search candidates.
 from math import gcd
 for b in [1,2,3,4]:
  coeff=np.rint(a*b).astype(int)
  if np.count_nonzero(coeff)==0:continue
  g=0
  for v in coeff:g=gcd(g,abs(int(v)))
  coeff//=max(1,g)
  if np.max(np.abs(a*b-coeff))<=0.12*b:
   return list(map(int,coeff))
 return list(map(int,np.rint(a*4)))

def fit(A,seed,steps):
 torch.set_num_threads(1);torch.manual_seed(seed)
 A=torch.as_tensor(A,dtype=torch.float64)
 A=A/(A.norm(dim=1,keepdim=True)+1e-9)
 w=torch.nn.Parameter(torch.randn(A.shape[1],dtype=torch.float64))
 w0=w.detach().clone();opt=torch.optim.Adam([w],lr=0.05)
 for i in range(steps):
  opt.zero_grad(); normed=w/(w.norm()+1e-10)
  loss=(A@normed).pow(2).mean() + 1e-3*(normed.abs().sum())
  loss.backward();opt.step()
 return w.detach()/w.detach().abs().max(),w0/w0.abs().max(),float(loss)

def original_3vc(head,pre,trans,post,names,candidate):
 iv=f'(and {candidate} {post})'; three=[f'(and {pre} (not {iv}))',f'(and {iv} {trans} (not {p.ren(iv,names)}))',f'(and {iv} (not {post}))']
 return p.check_batch(head,three)

def main():
 args=argparse.ArgumentParser();args.add_argument('--manifest',required=True,type=pathlib.Path);args.add_argument('--input',required=True,type=pathlib.Path);args.add_argument('--out',required=True,type=pathlib.Path);a=args.parse_args()
 mfest=json.loads(a.manifest.read_text()); assert len(mfest['cases'])>0
 allout=[];start=time.monotonic()
 for meta in mfest['cases']:
  file=meta['name']; t0=time.monotonic()
  row={'file':file,'path':meta['path'],'registered_blob_sha1':meta['sha'],'status':'UNKNOWN', 'learner':[]}
  try:
   filedata=(a.input/file).read_bytes();gitsha=hashlib.sha1(('blob '+str(len(filedata))+'\0').encode()+filedata).hexdigest()
   if gitsha!=meta['sha'] or len(filedata)!=meta['size']:raise RuntimeError('ORIGINAL_SOURCE_SHA_MISMATCH')
   raw=filedata.decode();names,fs,fns=p.parse(raw)
   if len(names)>5:raise RuntimeError('UNSUPPORTED_GT5_STATE')
   decl='\n'.join(f'(declare-const {v} Int)\n(declare-const {v}! Int)' for v in names)
   head='(set-logic LIA)\n'+decl+'\n'+'\n'.join(fs)+'\n'
   pre='('+fns[0]+' '+' '.join(names)+')'; trans='('+fns[1]+' '+' '.join(names+[v+'!' for v in names])+')';post='('+fns[2]+' '+' '.join(names)+')'
   rng=random.Random(45519)
   prs=query(head,pre,names,rng,'pre',32); ts=query(head,trans,names,rng,'trans',48)
   D=np.asarray([row[len(names):] for row in ts])-np.asarray([row[:len(names)] for row in ts]) if ts else np.empty((0,len(names)))
   B=np.asarray([np.subtract(q,prs[0]) for q in prs[1:]]) if len(prs)>1 else np.empty((0,len(names)))
   A=np.concatenate([D,B],axis=0).astype(float)
   AA=A.copy(); AA/=np.maximum(np.max(np.abs(AA),axis=0),1.)[None,:]
   row={'file':file,'state':names,'samples_pre':len(prs),'samples_trans':len(ts),'rank':int(np.linalg.matrix_rank(A)),'learner':[]}
   # STRONG exact same-pre/sample rational nullspace comparison, never hidden.
   m=sp.Matrix([[int(v) for v in r] for r in A]);null=m.nullspace();row['exact_nullspace_dim']=len(null)
   row['exact_same_samples'] = []
   for u in null:
    den=sp.ilcm(*[v.q for v in u]);co=[int(x*den) for x in u]
    from math import gcd
    g=0
    for v in co:g=gcd(g,abs(v))
    co=[x//max(g,1) for x in co]
    ii='(= '+expr(co,names)+' '+(str(int(np.dot(co,prs[0]))) if int(np.dot(co,prs[0]))>=0 else f'(- {-int(np.dot(co,prs[0]))})')+')'
    row['exact_same_samples'].append({'coeff':co,'vc':original_3vc(head,pre,trans,post,names,ii),'invariant':f'(and {ii} {post})'})
   for seed in range(4):
    ww,w0,loss=fit(A,seed,2000)
    co=quantize(ww); co0=quantize(w0)
    cx=expr(co,names);cx0=expr(co0,names)
    # anchor w dot state at first genuine source Pre sample
    c=int(np.dot(co,prs[0]));c0=int(np.dot(co0,prs[0]));lit=lambda x: str(x) if x>=0 else f'(- {-x})'
    inv=f'(= {cx} {lit(c)})';inv0=f'(= {cx0} {lit(c0)})'
    vc=original_3vc(head,pre,trans,post,names,inv);v0=original_3vc(head,pre,trans,post,names,inv0)
    row['learner'].append({'seed':seed,'weights':list(np.round(ww.numpy(),4)),'co':co,'original_vc':vc,'no_gradient_co':co0,'no_gradient_original_vc':v0,'loss':round(loss,7),'train_no_learn_basis':True, 'trained_invariant':f'(and {inv} {post})','untrained_invariant':f'(and {inv0} {post})'})
   for rec in row['learner']:
    rec['original_dual_pending']=rec['original_vc']==['unsat']*3
   row['status']='EXECUTED';row['elapsed_s']=round(time.monotonic()-t0,3)
  except Exception as e:
   row['error']=type(e).__name__+':'+str(e)[:200];row['elapsed_s']=round(time.monotonic()-t0,3)
  allout.append(row)
  print('FROZEN_LEARNED_FIRST',file,row['status'],sum(v.get('original_dual_pending',False) for v in row['learner']),len(row['learner']),row.get('error'),flush=True)

 report={'schema':'NEUMANN.Q3.first_src_body_gradient_conservation.v1','cohort':mfest.get('cohort'),'source_manifest_sha256':hashlib.sha256(a.manifest.read_bytes()).hexdigest(),'method':'actual 2000-step torch Adam source-local source-only self-supervision; no transferred weights; raw Pre+Trans only for fit; optional Post conjoined for exact source original 3VC','mathematical_class':'frozen integer affine combinations; exact nullspace strongest classical baseline','cases':allout,'wall_s':round(time.monotonic()-start,3),'global_Q3':'OPEN'}
 a.out.parent.mkdir(exist_ok=True,parents=True)
 a.out.write_text(json.dumps(report,indent=2)+'\n')
 print('FINAL_FIRST',a.out,'sha256',hashlib.sha256(a.out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()