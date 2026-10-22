#!/usr/bin/env python3
"""Source-only verified upper support K using candidate success under full source inductive conditions.
No winning k, human witness state or manually written invariant is accepted.

For each original program, retain candidate conjuncts with support <= K and check
original Init, Step, Post independently with libz3, smallest successful K admitted.
"""
import argparse, ctypes, hashlib, json, pathlib, re, sys, time

class Z3:
 def __init__(self):
  z=self.z=ctypes.CDLL('libz3.so.4')
  z.Z3_mk_config.restype=ctypes.c_void_p
  z.Z3_mk_context.argtypes=[ctypes.c_void_p];z.Z3_mk_context.restype=ctypes.c_void_p
  z.Z3_eval_smtlib2_string.argtypes=[ctypes.c_void_p,ctypes.c_char_p];z.Z3_eval_smtlib2_string.restype=ctypes.c_char_p
  z.Z3_del_context.argtypes=[ctypes.c_void_p];z.Z3_del_config.argtypes=[ctypes.c_void_p]
 def check(self,s):
  z=self.z;cf=z.Z3_mk_config();ctx=z.Z3_mk_context(cf)
  try:v=z.Z3_eval_smtlib2_string(ctx,s.encode()).decode().strip()
  finally:z.Z3_del_context(ctx);z.Z3_del_config(cf)
  if v not in ('sat','unsat'):raise RuntimeError('SMT_ERROR_OR_UNKNOWN: '+v[:200])
  return v

def atoms(e):
 e=e.strip()
 if not e.startswith('(and '):return [e]
 e=e[5:-1];i=0;res=[]
 while i<len(e):
  if e[i].isspace():i+=1;continue
  if e[i]!='(':raise ValueError('INVALID_ATOM '+e[i:i+30])
  start=i;level=0
  while i<len(e):
   level+=(e[i]=='(')-(e[i]==')');i+=1
   if not level:break
  if level:raise ValueError('UNBALANCED_ATOM')
  res.append(e[start:i])
 return res

def balanced(e,k):
 c=0
 for j in range(k,len(e)):
  c+=(e[j]=='(')-(e[j]==')')
  if c==0:return e[k:j+1]
 raise ValueError('UNBALANCED_FUN')

def original_vc(raw,terms,names):
 defs=[balanced(raw,m.start()) for m in re.finditer(r'\(define-fun\s+',raw)]
 if len(defs)!=3:raise ValueError('EXPECTED_3_DEFS')
 fn=[re.match(r'\(define-fun\s+([^\s()]+)',d).group(1) for d in defs]
 st=' '.join(names);ps=' '.join(name+'!' for name in names)
 pre='('+fn[0]+' '+st+')';trans='('+fn[1]+' '+st+' '+ps+')';post='('+fn[2]+' '+st+')'
 inv='(and '+' '.join(terms)+')' if terms else 'true'
 candidate='(define-fun Inv ('+' '.join('('+n+' Int)' for n in names)+') Bool '+inv+')'
 ds='\n'.join('(declare-const '+n+' Int)\n(declare-const '+n+'! Int)' for n in names)
 head='(set-logic LIA)\n'+ds+'\n'+'\n'.join(defs)+'\n'+candidate+'\n'
 v='(Inv '+st+')';vp='(Inv '+ps+')'
 return {tag:head+'(assert '+expr+')\n(check-sat)\n' for tag,expr in {
  'init':'(and '+pre+' (not '+v+'))',
  'consecution':'(and '+v+' '+trans+' (not '+vp+'))',
  'goal':'(and '+v+' (not '+post+'))',
 }.items()}

def main():
 p=argparse.ArgumentParser();p.add_argument('--proposals',required=True,type=pathlib.Path);p.add_argument('--source-dir',required=True,type=pathlib.Path);p.add_argument('--manifest',required=True,type=pathlib.Path);p.add_argument('--out',required=True,type=pathlib.Path)
 a=p.parse_args();t0=time.perf_counter();d=json.loads(a.proposals.read_text());m=json.loads(a.manifest.read_text());z=Z3()
 assert len(d['cases'])==len(m['cases'])
 rows=[];chosen={};queries=0
 for c,meta in zip(d['cases'],m['cases']):
  assert c['file']==meta['name'] and c['safe']
  raw=(a.source_dir/meta['name']).read_bytes()
  assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==meta['sha']
  body=raw.decode();match=re.search(r'\(synth-inv\s+[^\s()]+\s+',body)
  names=re.findall(r'\(\s*([^\s()]+)\s+Int\s*\)',balanced(body,match.end()))
  if not names:raise AssertionError('NO_STATE')
  aa=atoms(c['invariant'])
  tiers=[];kchosen=None
  for k in range(1,len(names)+1):
   kept=[atom for atom in aa if sum(name in set(re.findall(r'[A-Za-z_!][A-Za-z_0-9!]*',atom)) for name in names)<=k]
   vc=original_vc(body,kept,names)
   checks={}
   for stage,script in vc.items():
    status=z.check(script);queries+=1;checks[stage]=status
    if status!='unsat':break
   good=(len(checks)==3 and all(x=='unsat' for x in checks.values()))
   tiers.append({'k':k,'num_atoms':len(kept),'original_vc_results':checks,'admitted':good})
   if good:kchosen=k;break
  if kchosen is None:raise AssertionError('UNPROVEN_AUTOMATIC_UPPER '+meta['name'])
  chosen[meta['name']]=kchosen;rows.append({'source':meta['name'],'certified_upper_k':kchosen,'total_original_state_vars':len(names),'tiers':tiers,'source_sha':meta['sha']})
  print('UPPER_K_ORIGINAL_3VC_PROVEN',meta['name'],kchosen,'vc_queries',sum(len(t['original_vc_results']) for t in tiers),flush=True)
 result={'schema':'NEUMANN.Q4.source_only_minimal_upper_certificate.v1','proven_upper_k':chosen,'source_count':len(rows),'rows':rows,'z3_original_vc_queries':queries,'wall_s':round(time.perf_counter()-t0,5),'model_training':0,'search_cost_counted':True}
 a.out.parent.mkdir(exist_ok=True,parents=True);a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print('UPPER_PROVEN',json.dumps({'k':chosen,'queries':queries,'wall_s':result['wall_s']}),flush=True)
if __name__=='__main__':main()
