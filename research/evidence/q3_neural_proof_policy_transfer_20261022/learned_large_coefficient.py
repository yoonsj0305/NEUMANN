#!/usr/bin/env python3
"""Posthoc original-source structural learning beyond frozen {-1,0,1} coefficient vocabulary.

NO source basename conditional, NO manually provided invariant, NO gold samples.
Source Pre+Trans only used for state-row sampling and Adam learning.
Independent original Source 3VC is authority; exact rational same rows is strongest control.
All program sources were ALREADY OPENED in previous study. Claims are scoped.
"""
import argparse, hashlib, importlib.util, json, pathlib, random, re, time, math
from fractions import Fraction
from functools import reduce
import numpy as np
import torch
import sympy as sp

def load(path):
 spec=importlib.util.spec_from_file_location('old_classical',path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def parse_values(output, names):
 if not output or output[0]!='sat':return None
 s=' '.join(output[1:]);lst=[]
 for v in names:
  match=re.search(r'\('+re.escape(v)+r'\s+(\(-\s*\d+\s*\)|-?\d+)\)',s)
  if not match:return None
  q=match.group(1);lst.append(-int(re.findall(r'\d+',q)[0]) if q.startswith('(-') else int(q))
 return lst

def query_states(p,head,condition,names,rng,kind,count=32,bound=20000):
 names2=names+([n+'!' for n in names] if kind=='trans' else [])
 bound= min(20000,max(1000,bound))
 row=[];begin=time.monotonic()
 for i in range(count*8):
  name=names[i%len(names)];value=rng.randint(-2,50)
  pin='(assert (= '+name+' '+(str(value) if value>=0 else '(- '+str(-value)+')')+'))' if i%3 else ''
  recent=row[-16:]
  clauses=['(assert (not (and '+' '.join('(= '+v+' '+(str(x) if x>=0 else '(- '+str(-x)+')')+')' for v,x in zip(names2,t))+')))' for t in recent]
  bound_set=['(assert (and (>= '+v+' (- '+str(bound)+')) (<= '+v+' '+str(bound)+')))' for v in names2]
  original='\n'.join([head]+bound_set+['(assert '+condition+')',pin]+clauses)
  first=p.z.run(original+'\n(check-sat)')
  if first!=['sat']:continue
  out=p.z.run(original+'\n(check-sat)\n(get-value ('+' '.join(names2)+'))')
  vals=parse_values(out,names2)
  if vals is not None and vals not in row:row.append(vals)
  if len(row)>=count or time.monotonic()-begin>6:break
 return row

def integerize_numpy(x,max_den=64):
 x=np.asarray(x,dtype=np.float64)
 if not np.all(np.isfinite(x)) or np.max(np.abs(x))<1e-9:return [0]*len(x)
 x=x/np.max(np.abs(x))
 fr=[Fraction(float(v)).limit_denominator(max_den) for v in x]
 l=1
 for q in fr:l=math.lcm(l,q.denominator)
 v=[int(q*l) for q in fr];g=reduce(math.gcd,map(abs,v),0)
 if not g:return [0]*len(x)
 v=[w//g for w in v]
 if max(abs(y) for y in v)>3000:return [0]*len(x)
 return v

def expression(co,names):
 items=[]
 for w,n in zip(co,names):
  if w==0:continue
  if w==1:items.append(n)
  elif w==-1:items.append('(- '+n+')')
  elif w>0:items.append('(* '+str(w)+' '+n+')')
  else:items.append('(* (- '+str(-w)+') '+n+')')
 if not items:return '0'
 return items[0] if len(items)==1 else '(+ '+' '.join(items)+')'

def candidate(co,base,names):
 val=sum(int(w)*int(x) for w,x in zip(co,base));lit=str(val) if val>=0 else '(- '+str(-val)+')'
 return '(= '+expression(co,names)+' '+lit+')'

def train(A,seed,steps):
 torch.set_num_threads(1);torch.manual_seed(seed)
 t=torch.as_tensor(A,dtype=torch.float64)
 t=t/(t.norm(dim=1,keepdim=True)+1e-12)
 w=torch.nn.Parameter(torch.randn(A.shape[1],dtype=torch.float64))
 init=w.detach().numpy().copy();opt=torch.optim.Adam([w],lr=.06)
 for _ in range(steps):
  opt.zero_grad();u=w/(w.norm()+1e-12);loss=(t@u).square().mean();loss.backward();opt.step()
 return integerize_numpy(w.detach().numpy()),integerize_numpy(init),round(float(loss.detach()),10)

def certify(p,head,pre,trans,post,names,eq):
 inv='(and '+eq+' '+post+')'
 queries=[f'(and {pre} (not {inv}))',f'(and {inv} {trans} (not {p.ren(inv,names)}))',f'(and {inv} (not {post}))']
 vc=p.check_batch(head,queries)
 return vc, inv


def original_support_houdini(p,names,forms,head,pre,trans,post,eq=None):
    """Classical source-only inductive support search with original source literal bounds.

    The learned eq is a PROPOSAL, not an authority. Credit it only if retained
    in a final independently sufficient original source inductive conjunction.
    """
    tic=time.monotonic()
    pool=list(p.pred_pool(names,forms[0]+forms[1],max_support=4))
    num=set([-2,-1,0,1,2])
    for n in re.findall(r'(?<![a-zA-Z_0-9])\d+(?![a-zA-Z_0-9])',forms[0]+forms[1]):
        v=int(n)
        if v<=300:num.add(v)
    for v in names:
        for b in sorted(num):
            lit=str(b)
            pool.extend([f'(>= {v} {lit})',f'(<= {v} {lit})'])
    pool=list(dict.fromkeys(pool+[eq] if eq else pool))
    pool=list(dict.fromkeys(pool+[post]))
    calls=0
    init=p.check_batch(head,[f'(and {pre} (not {a}))' for a in pool]);calls+=len(init)
    keep=[a for a,x in zip(pool,init) if x=='unsat']
    loops=0
    for _ in range(8):
        loops+=1;conj=p.conj(keep)
        tests=p.check_batch(head,[f'(and {conj} {trans} (not {p.ren(x,names)}))' for x in keep]);calls+=len(tests)
        nxt=[x for x,t in zip(keep,tests) if t=='unsat']
        if len(nxt)==len(keep):keep=nxt;break
        keep=nxt
    inv=p.conj(keep)
    vc=p.check_batch(head,[f'(and {pre} (not {inv}))',f'(and {inv} {trans} (not {p.ren(inv,names)}))',f'(and {inv} (not {post}))']);calls+=3
    return {'safe_certified':vc==['unsat']*3,'original_3vc':vc,'invariant':inv if vc==['unsat']*3 else None,'eq_retained':bool(eq and eq in keep),'eq_proposal':eq,'pool_size':len(pool),'remaining':len(keep),'loops':loops,'solver_queries':calls,'elapsed_s':round(time.monotonic()-tic,4)}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--engine',type=pathlib.Path,required=True);ap.add_argument('--manifest',type=pathlib.Path,required=True);ap.add_argument('--source-dir',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args()
 p=load(a.engine);m=json.loads(a.manifest.read_text());root=time.monotonic();output=[]
 for meta in m['cases']:
  row={'file':meta['name'],'expected_sha':meta['sha'],'status':'UNKNOWN','trained':[],'no_gradient':[],'exact':[]};tic=time.monotonic()
  try:
   raw=(a.source_dir/meta['name']).read_bytes();assert len(raw)==meta['size'] and hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()==meta['sha'],'original mismatch'
   names,forms,fns=p.parse(raw.decode());decl='\n'.join(f'(declare-const {n} Int)\n(declare-const {n}! Int)' for n in names)
   head='(set-logic LIA)\n'+decl+'\n'+'\n'.join(forms)+'\n'
   pre='('+fns[0]+' '+' '.join(names)+')';trans='('+fns[1]+' '+' '.join(names+[n+'!' for n in names])+')';post='('+fns[2]+' '+' '.join(names)+')'
   max_lit=max([abs(int(x)) for x in re.findall(r'(?<![a-zA-Z_\d])\d+',forms[0]+forms[1])] or [30]);bound=min(20000,max(5000,max_lit*150))
   rng=random.Random(17552)
   pre_rows=query_states(p,head,pre,names,rng,'pre',32,bound);trans_rows=query_states(p,head,trans,names,rng,'trans',48,bound)
   if len(pre_rows)<2 or len(trans_rows)<2:raise RuntimeError('INSUFFICIENT_ORIGINAL_PRE_OR_TRANS_SAMPLES')
   A=np.asarray([[b-a for a,b in zip(t[:len(names)],t[len(names):])] for t in trans_rows]+[[b-a for a,b in zip(pre_rows[0],t)] for t in pre_rows[1:]],dtype=float)
   rank=np.linalg.matrix_rank(A);row.update(state_names=names,num_pre=len(pre_rows),num_trans=len(trans_rows),rank=int(rank),null_dim=int(len(names)-rank))
   pool=set(p.pred_pool(names,forms[0]+forms[1],max_support=4));row['frozen_pool_size']=len(pool)
   row['source_literal_support_only']=original_support_houdini(p,names,forms,head,pre,trans,post)
   for seed in range(4):
    co,co0,loss=train(A,seed,2500)
    for tag,vec in [('trained',co),('no_gradient',co0)]:
     if not any(vec):vc=['NO_RELATION'];inv=None;eq='true'
     else:eq=candidate(vec,pre_rows[0],names);vc,inv=certify(p,head,pre,trans,post,names,eq)
     support=original_support_houdini(p,names,forms,head,pre,trans,post,eq) if any(vec) else None
     row[tag].append(dict(seed=seed,coeff=vec,eq=eq,full_source_3vc=vc,accepted=vc==['unsat']*3,invariant=inv if vc==['unsat']*3 else None,with_classical_support=support,exact_predicate_outside_frozen_pool=eq not in pool,loss=loss if tag=='trained' else None))
   # Same exact samples, complete integer-rational coefficient subspace baseline.
   K=sp.Matrix([[int(v) for v in row_] for row_ in A]);null=K.nullspace();
   for idx,u in enumerate(null):
    l=1
    for val in u:l=sp.ilcm(l,val.q)
    co=[int(x*l) for x in u];g=reduce(math.gcd,map(abs,co),0);co=[v//g for v in co]
    eq=candidate(co,pre_rows[0],names);vc,inv=certify(p,head,pre,trans,post,names,eq)
    row['exact'].append(dict(index=idx,coeff=co,eq=eq,full_source_3vc=vc,accepted=vc==['unsat']*3,invariant=inv if vc==['unsat']*3 else None,with_classical_support=original_support_houdini(p,names,forms,head,pre,trans,post,eq),exact_predicate_outside_frozen_pool=eq not in pool))
   row['status']='EXECUTED'
  except Exception as ex:row['status']='ABSTAIN';row['reason']=type(ex).__name__+': '+str(ex)[:230]
  row['wall_s']=round(time.monotonic()-tic,4);output.append(row)
  print('ORIGINAL_TRAINED_COEFF',row['file'],row['status'],sum(x['accepted'] for x in row['trained']),sum(x['accepted'] for x in row['exact']),row.get('reason'),flush=True)
 report={'schema':'NEUMANN.Q3.original_source_large_coefficient_true_pytorch.v1','method':'Source Pre+Trans only; train 4 PyTorch CPU models 2500 steps, rational readout max denominator64, equal data exact nullspace and unchanged no-gradient, full original 3VC','cohort':'Previously source-opened posthoc true official originals. NO NEW FIRSTBLIND','source_manifest_sha256':hashlib.sha256(a.manifest.read_bytes()).hexdigest(),'cases':output,'wall_s':round(time.monotonic()-root,4),'global_Q3':'OPEN'}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')
 print('END',report['wall_s'],'sha256',hashlib.sha256(a.out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
