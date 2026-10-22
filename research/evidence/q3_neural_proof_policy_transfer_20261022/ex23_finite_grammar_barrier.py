#!/usr/bin/env python3
"""Exhaustive scoped HouDINi grammar exclusion with source-native independent SMT.

Proves NO inductive sufficient conjunction over the EXACT registered finite
predicate vocabulary can prove the full original safe ex23 program: enumerate
all grammar predicates implicitly via greatest inductive Houdini fixed point,
verify EVERY drop/retention on Z3 and independent cvc5, and independently show
full strongest fixed point fails original goal. Learned relation 36*y-z+c=0
outside the frozen vocabulary then has a separate positive original 3VC proof.
This is a grammar-relative lower bound, not general unsafety/universality.
"""
import argparse,hashlib,importlib.util,json,pathlib,re,subprocess,time,ctypes

SHA='ada3eae4e8e9f4368c2a3ca0d2ecb900624dc7f9'

def load(path):
 spec=importlib.util.spec_from_file_location('old_reusable_source',path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def cvc5(script):
 q=subprocess.run(['cvc5','--lang','smt2','--tlimit=6000'],capture_output=True,input=script,text=True,timeout=12)
 z=[x for x in q.stdout.splitlines() if x.strip() in ('sat','unsat','unknown')]
 if q.returncode or not z:raise RuntimeError('cvc5_failure '+q.stderr[-100:])
 return z[-1].strip()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--original',type=pathlib.Path,required=True);ap.add_argument('--engine',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);ap.add_argument('--dual',action='store_true');a=ap.parse_args()
 raw=a.original.read_bytes();blob=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest();assert blob==SHA and len(raw)==559
 p=load(a.engine);names,defs,fns=p.parse(raw.decode())
 head='(set-logic LIA)\n'+'\n'.join(f'(declare-const {x} Int)\n(declare-const {x}! Int)' for x in names)+'\n'+'\n'.join(defs)+'\n'
 pre='('+fns[0]+' '+' '.join(names)+')';trans='('+fns[1]+' '+' '.join(names+[x+'!' for x in names])+')';goal='('+fns[2]+' '+' '.join(names)+')'
 pool=list(p.pred_pool(names,defs[0]+defs[1],max_support=4))
 bound=set([-2,-1,0,1,2])
 for n in re.findall(r'(?<![a-zA-Z_0-9])\d+(?![a-zA-Z_0-9])',defs[0]+defs[1]):
  if int(n)<=300:bound.add(int(n))
 for v in names:
  for x in sorted(bound):pool.extend([f'(>= {v} {x})',f'(<= {v} {x})'])
 pool=list(dict.fromkeys(pool+[goal]));begin=time.monotonic();receipts=[]
 def check(clause,expect=None,label=''):
  script=head+'(assert '+clause+')\n(check-sat)\n'
  z=p.z.run(script);result=z[-1] if z else 'INVALID_Z3'
  c=cvc5(script) if a.dual else 'NOT_EXECUTED'
  if result not in ('sat','unsat') or a.dual and c!=result or expect and result!=expect:
   raise RuntimeError('ORIGINAL_CROSSBACKEND_MISMATCH '+label+' z3='+result+' cvc5='+c+' expected='+str(expect))
  receipts.append({'sha256':hashlib.sha256(script.encode()).hexdigest(),'status':result,'cvc5':c,'label':label})
  return result
 init=[]
 for j,predicate in enumerate(pool):
  q=check(f'(and {pre} (not {predicate}))',label='INIT_ATOM_'+str(j));
  if q=='unsat':init.append(predicate)
 kept=init;rounds=[]
 for k in range(9):
  conjunction=p.conj(kept);new=[];removed=[]
  for j,predicate in enumerate(kept):
   q=check(f'(and {conjunction} {trans} (not {p.ren(predicate,names)}))',label='INDUCT_'+str(k)+'_'+str(j))
   if q=='unsat':new.append(predicate)
   else:removed.append(predicate)
  rounds.append({'round':k,'before':len(kept),'removed':len(removed),'after':len(new),'drop_candidates':removed})
  kept=new
  if not removed:break
 else:raise RuntimeError('FIXED_POINT_CAP_EXCEEDED')
 strongest=p.conj(kept)
 for j,(label,q,expected) in enumerate([
  ('STRONGEST_INIT',f'(and {pre} (not {strongest}))','unsat'),
  ('STRONGEST_CONSECUTION',f'(and {strongest} {trans} (not {p.ren(strongest,names)}))','unsat'),
  ('STRONGEST_GOAL_COUNTEREXAMPLE',f'(and {strongest} (not {goal}))','sat')]):check(q,expect=expected,label=label)
 # The model-proposed relation is never listed as a frozen grammar atom.
 learned='(= (+ (* 36 y) (- z) c) 0)';assert learned not in pool
 report={'schema':'NEUMANN.Q3.real_ex23_complete_finite_predicate_grammar_impossibility_original_dual.v1','source_git_blob':blob,'grammar_pool_size':len(pool),'initial_valid':len(init),'greatest_inductive_fixed_point_size':len(kept),'rounds':rounds,'whole_source_goal_from_strongest':'SAT','mathematical_exclusion':'Any inductive invariant expressible as conjunction of predicates from the fixed pool is a subset of the greatest inductive post-fixed point. The strongest invariant admits a Post counterexample. Therefore no such conjunction proves the original source goal. This says nothing about predicates outside pool.','model_relation_is_outside_pool':True,'source_only_origin':'POSTHOC already-opened real SyGuS original','smt_dual':a.dual,'num_solver_queries_per_backend':len(receipts),'receipts':receipts,'wall_s':round(time.monotonic()-begin,4)}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
 print('GRAMMAR_HARD_WALL',len(pool),len(init),len(kept),[(x['before'],x['removed']) for x in rounds],'Q',len(receipts),'SHA256',hashlib.sha256(a.out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
