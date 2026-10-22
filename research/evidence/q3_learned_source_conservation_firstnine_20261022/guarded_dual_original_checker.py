#!/usr/bin/env python3
"""Independently parse original SyGuS Pre/Trans/Post and dual-check learned guarded AST.
No reliance on learner Z3 proof dispositions, intentionally checks invalid candidates too.
"""
import argparse,hashlib,json,pathlib,subprocess
import independent_dual_checker as C

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--receipt',required=True);p.add_argument('--expected-gitblob',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 raw=pathlib.Path(a.source).read_bytes();got=hashlib.sha1(('blob '+str(len(raw))+'\0').encode()+raw).hexdigest()
 if got!=a.expected_gitblob:raise RuntimeError('ORIGINAL_SHA_MISMATCH')
 fun,names,forms=C.parse(raw.decode());h='(set-logic LIA)\n'+'\n'.join(f'(declare-const {n} Int)\n(declare-const {n}! Int)' for n in names)+'\n'+'\n'.join(forms)+'\n'
 pre='('+fun[0]+' '+' '.join(names)+')';trans='('+fun[1]+' '+' '.join(names+[n+'!' for n in names])+')';post='('+fun[2]+' '+' '.join(names)+')'
 rep=json.loads(pathlib.Path(a.receipt).read_text());out=[];tot={'trained':0,'no_training':0,'exact_rational':0,'pairs_checked':0,'z3_queries':0,'cvc5_queries':0}
 for row in rep['guards']:
  if row['status']!='EXECUTED':out.append({'guard':row['guard'],'status':row['status']});continue
  for t in list(row['methods'])+list(row['strong_exact_same_samples']):
   method=t.get('method','exact_rational');candidate=t['candidate']
   define='(define-fun I ('+' '.join('('+n+' Int)' for n in names)+') Bool '+candidate+')\n'
   iv='(I '+' '.join(names)+')';nxt='(I '+' '.join(n+'!' for n in names)+')'
   cond=[f'(and {pre} (not {iv}))',f'(and {iv} {trans} (not {nxt}))',f'(and {iv} (not {post}))']
   prove=[]
   for name,expr in zip(('init','consecution','goal'),cond):
    s=h+define+'(assert '+expr+')\n(check-sat)\n';z=C.z.run(s)
    cv=subprocess.run(['cvc5','--lang=smt2','--tlimit=6000'],input=s,text=True,capture_output=True,timeout=12)
    cc=cv.stdout.strip().splitlines()[-1] if cv.stdout.strip() else 'ERROR_'+cv.stderr[-50:]
    tot['z3_queries']+=1;tot['cvc5_queries']+=1
    prove.append({'stage':name,'z3':z,'cvc5':cc,'smt2_sha256':hashlib.sha256(s.encode()).hexdigest()})
   good=all(q['z3']=='unsat' and q['cvc5']=='unsat' for q in prove)
   tot['pairs_checked']+=1
   if good:
    if method=='trained':tot['trained']+=1
    elif method=='same_init_no_train':tot['no_training']+=1
    else:tot['exact_rational']+=1
   out.append({'guard':row['guard'],'seed':t.get('seed'),'method':method,'accepted':good,'original_3vc':prove,'candidate_sha256':hashlib.sha256(candidate.encode()).hexdigest()})
 result={'status':'FULL_EXECUTION_COMPLETE','original_gitblob_sha1':got,'learner_receipt_sha256':hashlib.sha256(pathlib.Path(a.receipt).read_bytes()).hexdigest(),'original_dual_full_source':out,'counts':tot,'global_Q3':'OPEN','scope':'posthoc original; learned grounded guarded AST but supplied guard/implication operator; stronger exact classical same-source comparator'}
 pathlib.Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print('DUAL_GUARD_CONSERVATION',tot,flush=True)
if __name__=='__main__':main()