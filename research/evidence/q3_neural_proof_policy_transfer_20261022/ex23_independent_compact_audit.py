#!/usr/bin/env python3
"""Source-authentic posthoc independent compact proof and necessity ablations.

This is a certificate auditor, NOT a trained model or generative proposer.
Original benchmark must be authenticated before substituting the externally
learned and greedily minimized candidate; original full Init/Consecution/Goal
are checked independently in Z3 and cvc5. Strong exact baseline also found it.
"""
import argparse,ctypes,hashlib,json,pathlib,re,subprocess,time

SHA='ada3eae4e8e9f4368c2a3ca0d2ecb900624dc7f9'

def balanced(s,k):
 d=0
 for j in range(k,len(s)):
  d+=(s[j]=='(')-(s[j]==')')
  if d==0:return s[k:j+1]
 raise RuntimeError('bad source')

def z3(script):
 z=ctypes.CDLL('libz3.so.4')
 z.Z3_mk_config.restype=ctypes.c_void_p;z.Z3_mk_context.argtypes=[ctypes.c_void_p];z.Z3_mk_context.restype=ctypes.c_void_p
 z.Z3_eval_smtlib2_string.argtypes=[ctypes.c_void_p,ctypes.c_char_p];z.Z3_eval_smtlib2_string.restype=ctypes.c_char_p
 z.Z3_del_context.argtypes=[ctypes.c_void_p];z.Z3_del_config.argtypes=[ctypes.c_void_p]
 cfg=z.Z3_mk_config();ctx=z.Z3_mk_context(cfg)
 try:q=z.Z3_eval_smtlib2_string(ctx,script.encode());out=q.decode() if q else ''
 finally:z.Z3_del_context(ctx);z.Z3_del_config(cfg)
 return out.strip()

def status(text):
 return next((k.strip() for k in text.splitlines() if k.strip() in ('sat','unsat','unknown')),'NO_SMT_STATUS')

def main():
 a=argparse.ArgumentParser();a.add_argument('--original',type=pathlib.Path,required=True);a.add_argument('--out',type=pathlib.Path,required=True);a.add_argument('--dual',action='store_true');x=a.parse_args()
 raw=x.original.read_bytes();gitsha=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest();assert gitsha==SHA and len(raw)==559
 src=raw.decode();fs=[balanced(src,m.start()) for m in re.finditer(r'\(define-fun\s+',src)];assert len(fs)==3
 fn=[re.search(r'\(define-fun\s+(\S+)',d).group(1) for d in fs]
 names=['y','z','c'];ds='\n'.join(f'(declare-const {v} Int)\n(declare-const {v}! Int)' for v in names)
 pre='('+fn[0]+' y z c)';trans='('+fn[1]+' y z c y! z! c!)';post='('+fn[2]+' y z c)'
 bounds='(<= y 127)';eq='(= (+ (* 36 y) (- z) c) 0)'
 cases={'FULL':[bounds,eq,post],'REMOVE_BOUND':[eq,post],'REMOVE_LEARNED_EQ':[bounds,post],'REMOVE_POST':[bounds,eq], 'MUTATE_COEFF_35':[bounds,'(= (+ (* 35 y) (- z) c) 0)',post], 'MUTATE_COEFF_37':[bounds,'(= (+ (* 37 y) (- z) c) 0)',post]}
 expected={'FULL':['unsat','unsat','unsat'],'REMOVE_BOUND':['unsat','sat','unsat'],'REMOVE_LEARNED_EQ':['unsat','sat','unsat'],'REMOVE_POST':['unsat','unsat','sat'],'MUTATE_COEFF_35':['sat','unsat','unsat'],'MUTATE_COEFF_37':['sat','sat','unsat']}
 head='(set-logic LIA)\n'+ds+'\n'+'\n'.join(fs)+'\n';out=[];start=time.monotonic()
 for case,clauses in cases.items():
  inv='(and '+' '.join(clauses)+')'
  def shifted(s):return re.sub(r'(?<![\w!])(y|z|c)(?![\w!])',lambda m:m.group(0)+'!',s)
  tests=[f'(and {pre} (not {inv}))',f'(and {inv} {trans} (not {shifted(inv)}))',f'(and {inv} (not {post}))']
  for i,body in enumerate(tests):
   smt=head+'(assert '+body+')\n(check-sat)\n';q=z3(smt);r=status(q)
   cvc='NOT_EXECUTED'
   if x.dual:
    p=subprocess.run(['cvc5','--lang','smt2','--tlimit=6000'],input=smt,capture_output=True,text=True,timeout=12)
    cvc=status(p.stdout)
   want=expected[case][i]
   if r!=want or x.dual and cvc!=want:raise RuntimeError(f'WRONG_{case}_{i}_{r}_{cvc}_want_{want}')
   out.append({'case':case,'VC':['init','consecution','goal'][i],'expected':want,'z3':r,'cvc5':cvc,'sha256':hashlib.sha256(smt.encode()).hexdigest()})
  print('COMPACT_PROOF',case,expected[case],flush=True)
 ledger={'schema':'NEUMANN.Q3.original_source_ex23_compact_certificate_and_mutation_dual.v1','authentic_source_git_blob':SHA,'source_size':len(raw),'manually_audited_after_learning':True,'coefficient_unique_in_family':'For any k, source Pre has y=1,z=36,c=0; Pre implies k*y-z+c=0 only if k=36','checks':out,'n_checks':len(out),'wall_s':round(time.monotonic()-start,4),'global_Q3':'OPEN'}
 x.out.parent.mkdir(parents=True,exist_ok=True);x.out.write_text(json.dumps(ledger,indent=2,sort_keys=True)+'\n')
 print('AUDIT_SHA256',hashlib.sha256(x.out.read_bytes()).hexdigest())
if __name__=='__main__':main()
