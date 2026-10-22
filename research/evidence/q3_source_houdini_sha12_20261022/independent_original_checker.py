#!/usr/bin/env python3
"""Independent full-original-SyGuS-3VC proof checker for generated invariants.
Only returns certified if exact full source Init/Consecution/Goal are UNSAT
in BOTH Z3 and independently pinned cvc5. No reliance on search engine.
"""
import argparse, json, pathlib, hashlib, re, ctypes, subprocess, time
class Z:
 def __init__(self):
  x=ctypes.CDLL('libz3.so.4');self.z=x;x.Z3_mk_config.restype=ctypes.c_void_p;x.Z3_mk_context.argtypes=[ctypes.c_void_p];x.Z3_mk_context.restype=ctypes.c_void_p;x.Z3_eval_smtlib2_string.argtypes=[ctypes.c_void_p,ctypes.c_char_p];x.Z3_eval_smtlib2_string.restype=ctypes.c_char_p;x.Z3_del_context.argtypes=[ctypes.c_void_p];x.Z3_del_config.argtypes=[ctypes.c_void_p]
 def check(self,s):
  z=self.z;cf=z.Z3_mk_config();ctx=z.Z3_mk_context(cf)
  try:
   q=z.Z3_eval_smtlib2_string(ctx,s.encode()); r=q.decode().strip() if q else 'UNKNOWN'
  finally:z.Z3_del_context(ctx);z.Z3_del_config(cf)
  return r
z=Z()
def gitsha(b):return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def balanced(s,k):
 balance=0
 for j in range(k,len(s)):
  balance+=int(s[j]=='(')-int(s[j]==')')
  if balance==0:return s[k:j+1]
 raise ValueError('truncated')
def main():
 p=argparse.ArgumentParser();p.add_argument('--receipt',type=pathlib.Path,required=True);p.add_argument('--input',type=pathlib.Path,required=True);p.add_argument('--manifest',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--backend',choices=['dual','z3'],default='dual');a=p.parse_args();beg=time.monotonic()
 initial=json.loads(a.receipt.read_text());manifest=json.loads(a.manifest.read_text());assert len(initial['cases'])==len(manifest['cases'])
 results=[];tot={'original_checked':0,'dual_safe_certified':0,'z3_safe_certified':0,'unsupported_or_unknown':0,'unsat_vc':0,'negative_controls':0,'q_z3':0,'q_cvc5':0}
 def check(script,expected):
  h=hashlib.sha256(script.encode()).hexdigest();now=time.monotonic();r=z.check(script);zm=(time.monotonic()-now)*1000;tot['q_z3']+=1
  if r!=expected:raise RuntimeError('INDEPENDENT_Z3_'+str(r)+'_EXPECTED_'+expected)
  result={'sha256':h,'expected':expected,'Z3':r,'z3_ms':round(zm,3)}
  if a.backend=='dual':
   now=time.monotonic();t=subprocess.run(['cvc5','--lang','smt2','--tlimit=6000'],input=script,text=True,capture_output=True,timeout=12)
   good=[k.strip() for k in t.stdout.splitlines() if k.strip() in ('sat','unsat','unknown')]
   cv=good[-1] if good else 'INVALID_'+t.stderr[-100:];tot['q_cvc5']+=1
   if cv!=expected:raise RuntimeError('INDEPENDENT_CVC5_'+cv+'_EXPECTED_'+expected)
   result.update(cvc5=cv,cvc5_ms=round((time.monotonic()-now)*1000,3))
  return result
 for record,meta in zip(initial['cases'],manifest['cases']):
  assert record['file']==meta['name']
  row={'name':meta['name'],'expected_gitblob':meta['sha'],'original_path':meta['path'],'source_route':record.get('source_algorithm'),'proposed':record.get('safe_certified',False)}
  try:
   raw=(a.input/meta['name']).read_bytes()
   if gitsha(raw)!=meta['sha']:raise RuntimeError('IMMUTABLE_ORIGINAL_MISMATCH')
   s=raw.decode(); defs=[balanced(s,m.start()) for m in re.finditer(r'\(define-fun\s+',s)]
   if len(defs)!=3:raise RuntimeError('UNSUPPORTED_SOURCE_DEFINITION_COUNT')
   fns=[re.match(r'\(define-fun\s+([^\s()]+)',d).group(1) for d in defs]
   parsed=re.search(r'\(synth-inv\s+[^\s()]+\s+',s)
   sig=balanced(s,parsed.end());names=re.findall(r'\(\s*([^\s()]+)\s+Int\s*\)',sig)
   if not names:raise RuntimeError('NO_STATE_VARS')
   ds='\n'.join('(declare-const '+x+' Int)\n(declare-const '+x+'! Int)' for x in names)
   head='(set-logic LIA)\n'+ds+'\n'+'\n'.join(defs)+'\n'
   prem='('+fns[0]+' '+' '.join(names)+')';tr='('+fns[1]+' '+' '.join(names+[v+'!' for v in names])+')';goal='('+fns[2]+' '+' '.join(names)+')'
   row.update(original_byte_len=len(raw),original_verified=True)
   tot['original_checked']+=1
   if not record.get('safe_certified') or not record.get('invariant'):
    tot['unsupported_or_unknown']+=1;row['status']='ABSTAIN_NO_PROPOSAL';results.append(row);continue
   inv=record['invariant']
   fun='(define-fun candidate ('+' '.join('('+x+' Int)' for x in names)+') Bool '+inv+')'
   iv='(candidate '+' '.join(names)+')';ivp='(candidate '+' '.join(x+'!' for x in names)+')'
   obligations={'init':f'(and {prem} (not {iv}))','consecution':f'(and {iv} {tr} (not {ivp}))','safety':f'(and {iv} (not {goal}))'}
   outputs={}
   for stage,form in obligations.items():
    script=head+fun+'\n(assert '+form+')\n(check-sat)\n'
    outputs[stage]=check(script,'unsat');tot['unsat_vc']+=1
   for tag,expr in [('FALSE_INIT','(and '+prem+' (not false))'),('TRUE_GOAL','(not '+goal+')')]:
    outputs[tag]=check(head+'\n(assert '+expr+')\n(check-sat)\n','sat');tot['negative_controls']+=1
   tot['z3_safe_certified']+=1
   if a.backend=='dual':tot['dual_safe_certified']+=1
   row.update(status='DUAL_ORIGINAL_SAFE_CERTIFIED' if a.backend=='dual' else 'Z3_ORIGINAL_SAFE_CERTIFIED',certificates=outputs,candidate_sha256=hashlib.sha256(inv.encode()).hexdigest())
  except Exception as ex:
   row.update(status='ABSTAIN_OR_FAIL',reason=type(ex).__name__+':'+str(ex)[:300]);tot['unsupported_or_unknown']+=1
  results.append(row)
  print('SOURCE_INDEPENDENT_VERDICT',row['name'],row['status'],flush=True)
 o={'schema':'NEUMANN.Q3.strong_classical_dual_original_full_recheck.v1','basis':'frozen generic zero-training source-only candidate proposer, proof authority independently reconstructed','checker':'Z3+pin-cvc5' if a.backend=='dual' else 'Z3-only','manifest_sha256':hashlib.sha256(a.manifest.read_bytes()).hexdigest(),'candidate_receipt_sha256':hashlib.sha256(a.receipt.read_bytes()).hexdigest(),'totals':tot,'rows':results,'wall_s':round(time.monotonic()-beg,3),'global_Q1_Q7':'OPEN'}
 a.out.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print('INDEPENDENT_SUMMARY',tot, 'SHA256',hashlib.sha256(a.out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()