#!/usr/bin/env python3
"""SOURCE-AUTHENTIC POSTHOC DEV. Actual guarded relation learning from source-only Pre/Trans.
No source-specific formula, coefficient, state variable name, human invariant or selected guard in code.
Does NOT attribute a new guard-operator primitive to the learned network.
"""
import argparse,hashlib,json,math,pathlib,random,re,time,sys
import numpy as np, torch, sympy as sp
import learned_source_conservation as L

def main():
 a=argparse.ArgumentParser();a.add_argument('--source',required=True);a.add_argument('--expected-gitblob',required=True);a.add_argument('--out',required=True);args=a.parse_args()
 t0=time.monotonic();source=pathlib.Path(args.source);raw=source.read_bytes()
 gitsha=hashlib.sha1(('blob '+str(len(raw))+'\0').encode()+raw).hexdigest()
 if gitsha!=args.expected_gitblob:raise RuntimeError('ORIGINAL_SOURCE_GITBLOB_MISMATCH')
 names,forms,fn=L.p.parse(raw.decode())
 header='(set-logic LIA)\n'+'\n'.join('(declare-const '+v+' Int)\n(declare-const '+v+'! Int)' for v in names)+'\n'+'\n'.join(forms)+'\n'
 pre='('+fn[0]+' '+' '.join(names)+')';trans='('+fn[1]+' '+' '.join(names+[v+'!' for v in names])+')';post='('+fn[2]+' '+' '.join(names)+')'
 guards=sorted(set((x,int(v)) for x,v in re.findall(r'\(=\s+(\w+)\s+(\d+)\)',forms[1]) if x in names and int(v)<=3))
 rows=[]
 for guard,val in guards:
  term=f'(= {guard} {val})'
  predata=L.query(header,f'(and {pre} {term})',names,random.Random(45519),'pre',32)
  transdata=L.query(header,f'(and {trans} {term})',names,random.Random(45519),'trans',48)
  if not predata or not transdata:
   rows.append({'guard':term,'status':'ABSTAIN_NO_SOURCE_SAT_SAMPLES','pre_count':len(predata),'trans_count':len(transdata)});continue
  D=np.asarray([z[len(names):] for z in transdata])-np.asarray([z[:len(names)] for z in transdata])
  active=[i for i,v in enumerate(names) if v!=guard and np.any(D[:,i]!=0)]
  if not 2<=len(active)<=4:
   rows.append({'guard':term,'status':'ABSTAIN_ACTIVE_ARITY','pre_count':len(predata),'trans_count':len(transdata),'active_count':len(active)});continue
  B=np.asarray([np.subtract(q,predata[0]) for q in predata[1:]]) if len(predata)>1 else np.empty((0,len(names)))
  A=np.concatenate([D[:,active],B[:,active]]).astype(float)
  rnk=int(np.linalg.matrix_rank(A))
  if rnk!=len(active)-1:
   rows.append({'guard':term,'status':'ABSTAIN_NO_UNIQUE_AFFINE_SUBSPACE','rank':rnk,'active_count':len(active)});continue
  out={'guard':term,'status':'EXECUTED','dynamic_vars':[names[i] for i in active],'samples_pre':len(predata),'samples_trans':len(transdata),'rank':rnk,'methods':[]}
  def compile_coeff(co):
   expr=L.expr(co,[names[i] for i in active]);c=int(np.dot(co,np.asarray(predata[0])[active]));val=str(c) if c>=0 else f'(- {-c})'
   rel=f'(=> {term} (= {expr} {val}))'
   return f'(and {rel} {post})'
  exact=sp.Matrix([[int(y) for y in row] for row in A]).nullspace()
  out['strong_exact_same_samples']=[]
  for e in exact:
   denom=sp.ilcm(*[v.q for v in e]);co=[int(v*denom) for v in e]
   g=math.gcd(*co) or 1;co=[v//g for v in co]
   inv=compile_coeff(co);vcs=L.p.check_batch(header,[f'(and {pre} (not {inv}))',f'(and {inv} {trans} (not {L.p.ren(inv,names)}))',f'(and {inv} (not {post}))'])
   out['strong_exact_same_samples'].append({'coeff':co,'candidate':inv,'original_vc':vcs})
  for seed in range(4):
   fit,init,loss=L.fit(A,seed,2000)
   for method,w in [('trained',fit),('same_init_no_train',init)]:
    co=L.quantize(w);inv=compile_coeff(co)
    vcs=L.p.check_batch(header,[f'(and {pre} (not {inv}))',f'(and {inv} {trans} (not {L.p.ren(inv,names)}))',f'(and {inv} (not {post}))'])
    out['methods'].append({'seed':seed,'method':method,'coeff':co,'candidate':inv,'original_vc':vcs,'loss':round(loss,8) if method=='trained' else None})
  rows.append(out)
  print('GUARDED_DEV',term,'train',sum(v['original_vc']==['unsat']*3 for v in out['methods'] if v['method']=='trained'),'nograd',sum(v['original_vc']==['unsat']*3 for v in out['methods'] if v['method']=='same_init_no_train'),'exact',sum(v['original_vc']==['unsat']*3 for v in out['strong_exact_same_samples']),flush=True)
 result={'schema':'NEUMANN.Q3.guard_source_conditioned_learned_conservation.original_development.v1','scope':'posthoc previously opened original; no firstblind','original_path':str(source),'original_git_sha':gitsha,'original_sha256':hashlib.sha256(raw).hexdigest(),'source_definition_count':len(forms),'guards':rows,'elapsed_s':round(time.monotonic()-t0,3),'model':'REAL torch Adam 2000 steps, four seeds, local source-only training; same-init no grad; strong exact nullspace','global_Q1_Q7':'OPEN'}
 pathlib.Path(args.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()