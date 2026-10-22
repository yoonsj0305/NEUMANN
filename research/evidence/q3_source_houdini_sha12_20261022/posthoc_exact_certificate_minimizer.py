#!/usr/bin/env python3
"""Posthoc sound certificate minimization, independent original 3VC unchanged.
Designed for replay on archived frozen outputs; no source-specific invariants.
"""
import argparse,collections,hashlib,json,pathlib,re,time
# reuse already frozen exact SMT query library, not its candidate choices
from classical_houdini import parse,check_batch,ren,conj

def split_conj(x):
 x=x.strip()
 if not x.startswith('(and '):return [x]
 inside=x[5:-1].strip();out=[];balance=0;start=None
 for i,ch in enumerate(inside):
  if ch=='(':
   if balance==0:start=i
   balance+=1
  elif ch==')':
   balance-=1
   if balance==0:out.append(inside[start:i+1])
 assert balance==0 and len(out)>0
 return out

def certify(source,names,pre,tr,post,atoms):
 expr=conj(atoms);qs=[f'(and {pre} (not {expr}))',f'(and {expr} {tr} (not {ren(expr,names)}))',f'(and {expr} (not {post}))']
 return check_batch(source,qs)

def main():
 a=argparse.ArgumentParser();a.add_argument('--receipt',required=True);a.add_argument('--input',required=True);a.add_argument('--out',required=True);a.add_argument('--max-tests',type=int,default=1000);v=a.parse_args();records=json.load(open(v.receipt))['cases'];out=[];t0=time.monotonic()
 for r in records:
  p=pathlib.Path(v.input,r['file']);t=time.monotonic()
  row={'original_name':r['file'],'original_sha256':r.get('original_sha256'),'prior_certified':r['safe_certified'],'prior_conjunct_count':r.get('num_conjuncts'),'attempts':0}
  try:
   if not r['safe_certified'] or not r.get('invariant'):raise RuntimeError('NO_CERTIFIED_ORIGINAL_CANDIDATE')
   raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==r['original_sha256']
   names,forms,fns=parse(raw.decode());ds='\n'.join(f'(declare-const {x} Int)\n(declare-const {x}! Int)' for x in names)
   head='(set-logic LIA)\n'+ds+'\n'+'\n'.join(forms)+'\n'
   pre='('+fns[0]+' '+' '.join(names)+')';trans='('+fns[1]+' '+' '.join(names+[s+'!' for s in names])+')';post='('+fns[2]+' '+' '.join(names)+')'
   atoms=split_conj(r['invariant']);assert len(atoms)==r['num_conjuncts']
   precheck=certify(head,names,pre,trans,post,atoms);row['attempts']+=1
   assert precheck==['unsat']*3
   shortest=atoms
   for order in [lambda xx:xx,lambda xx:list(reversed(xx)),lambda xx:sorted(xx,key=len,reverse=True)]:
    cur=list(atoms)
    for candidate in order(atoms):
     if candidate not in cur:continue
     if row['attempts']>=v.max_tests:break
     next_list=cur.copy();next_list.remove(candidate)
     if not next_list:continue
     outcomes=certify(head,names,pre,trans,post,next_list);row['attempts']+=1
     if outcomes==['unsat']*3:cur=next_list
    if len(cur)<len(shortest):shortest=cur
   final=certify(head,names,pre,trans,post,shortest);row['attempts']+=1
   assert final==['unsat']*3
   reduced=conj(shortest)
   row.update(status='EXACT_3VC_MINIMIZED',final_conjunct_count=len(shortest),minimized_invariant=reduced,original_invariant_chars=len(r['invariant']),minimized_invariant_chars=len(reduced),original_3vc=final)
  except Exception as ex:
   row.update(status='ABSTAIN',reason=type(ex).__name__+':'+str(ex)[:180]);
  row['wall_s']=round(time.monotonic()-t,3);out.append(row)
  print('PROOF_MINIMUM',r['file'],row['status'],r.get('num_conjuncts'),'->',row.get('final_conjunct_count'),'tests',row['attempts'],'wall',row['wall_s'],flush=True)
 result={'schema':'neumann.q3.classical_posthoc_cert_compaction.first_v1','scope':'Previously opened dev8 or already frozen SHA12; no learning, independent cvc5 replay required','cases':out,'sum_original_conjuncts':sum(r.get('prior_conjunct_count') or 0 for r in out),'sum_minimal_conjuncts':sum(r.get('final_conjunct_count') or 0 for r in out),'certified':sum(r['status']=='EXACT_3VC_MINIMIZED' for r in out),'total_wall_s':round(time.monotonic()-t0,3),'global_Q4':'OPEN'}
 pathlib.Path(v.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print('SUMMARY',result['certified'],'/',len(out),'atoms',result['sum_original_conjuncts'],'->',result['sum_minimal_conjuncts'],'wall',result['total_wall_s'],'sha',hashlib.sha256(pathlib.Path(v.out).read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()