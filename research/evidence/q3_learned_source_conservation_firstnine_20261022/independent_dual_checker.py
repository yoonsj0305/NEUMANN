#!/usr/bin/env python3
"""Independent authored full original 3VC verifier for ALL proof arms, never uses learner source parser."""
import argparse,hashlib,json,pathlib,re,subprocess,ctypes,time
class Z3:
 def __init__(self):
  z=ctypes.CDLL('libz3.so.4'); self.z=z
  z.Z3_mk_config.restype=ctypes.c_void_p
  z.Z3_mk_context.argtypes=[ctypes.c_void_p];z.Z3_mk_context.restype=ctypes.c_void_p
  z.Z3_eval_smtlib2_string.argtypes=[ctypes.c_void_p,ctypes.c_char_p];z.Z3_eval_smtlib2_string.restype=ctypes.c_char_p
  z.Z3_del_context.argtypes=[ctypes.c_void_p];z.Z3_del_config.argtypes=[ctypes.c_void_p]
 def run(self,s):
  z=self.z;cfg=z.Z3_mk_config();ctx=z.Z3_mk_context(cfg)
  try:
   out=z.Z3_eval_smtlib2_string(ctx,s.encode());return out.decode().strip() if out else 'NULL'
  finally:z.Z3_del_context(ctx);z.Z3_del_config(cfg)
z=Z3()
def expression(s,i):
 depth=0
 for k in range(i,len(s)):
  depth+=int(s[k]=='(')-int(s[k]==')')
  if depth==0:return s[i:k+1]
 raise RuntimeError('UNBALANCED_ORIGINAL')
def parse(s):
 forms=[expression(s,m.start()) for m in re.finditer(r'\(define-fun\s+',s)]
 if len(forms)!=3: raise RuntimeError('DEFINE_FUN_COUNT_'+str(len(forms)))
 funcs=[re.search(r'\(define-fun\s+([^\s(]+)',x).group(1) for x in forms]
 m=re.search(r'\(synth-inv\s+[^\s()]+\s+',s)
 if not m:raise RuntimeError('NO_SYNTH_INV')
 sig=expression(s,m.end());names=re.findall(r'\(\s*([^\s()]+)\s+Int\s*\)',sig)
 if not names:raise RuntimeError('NO_INTEGER_STATES')
 return funcs,names,forms

def main():
 pa=argparse.ArgumentParser();pa.add_argument('--manifest',required=True);pa.add_argument('--input',required=True);pa.add_argument('--receipt',required=True);pa.add_argument('--out',required=True);pa.add_argument('--dual',action='store_true');a=pa.parse_args()
 m=json.loads(pathlib.Path(a.manifest).read_text());raw=json.loads(pathlib.Path(a.receipt).read_text())
 assert len(m['cases'])==len(raw['cases'])==9
 r=[];tot={'cases':0,'candidates':0,'z3_3vc':0,'cvc5_3vc':0,'truly_independent_dual':0,'mutant_true_sat':0,'mutant_false_sat':0,'source_identity_match':0}
 for reg,item in zip(m['cases'],raw['cases']):
  row={'source':reg['name'],'trained':[],'initialization_only':[],'exact_rational':[],'case_errors':[]}
  try:
   assert item['file']==reg['name']
   buf=(pathlib.Path(a.input)/reg['name']).read_bytes()
   assert len(buf)==reg['size']
   assert hashlib.sha1(('blob '+str(len(buf))+'\0').encode()+buf).hexdigest()==reg['sha']
   tot['source_identity_match']+=1
   funcs,names,defs=parse(buf.decode())
   declarations='\n'.join('(declare-const '+v+' Int)\n(declare-const '+v+'! Int)' for v in names)
   hdr='(set-logic LIA)\n'+declarations+'\n'+'\n'.join(defs)+'\n'
   pre='('+funcs[0]+' '+' '.join(names)+')';tr='('+funcs[1]+' '+' '.join(names+[v+'!' for v in names])+')';post='('+funcs[2]+' '+' '.join(names)+')'
   def verify(inv):
    form='(define-fun exact_candidate ('+' '.join('('+n+' Int)' for n in names)+') Bool '+inv+')\n'
    iv='(exact_candidate '+' '.join(names)+')';ivp='(exact_candidate '+' '.join(n+'!' for n in names)+')'
    vcs=[f'(and {pre} (not {iv}))',f'(and {iv} {tr} (not {ivp}))',f'(and {iv} (not {post}))']
    outcomes=[]
    for stage,cond in zip(['init','consecution','safety'],vcs):
     scr=hdr+form+'(assert '+cond+')\n(check-sat)\n'
     zz=z.run(scr);tot['z3_3vc']+=1
     if a.dual:
      resp=subprocess.run(['cvc5','--lang=smt2','--tlimit=6000'],input=scr,text=True,capture_output=True,timeout=12)
      cc=resp.stdout.strip().splitlines()[-1] if resp.stdout.strip() else 'ERROR_'+resp.stderr[-60:];tot['cvc5_3vc']+=1
     else:cc='NOT_EXECUTED'
     outcomes.append({'stage':stage,'Z3':zz,'cvc5':cc,'sha256':hashlib.sha256(scr.encode()).hexdigest()})
    accepted=all(v['Z3']=='unsat' and (not a.dual or v['cvc5']=='unsat') for v in outcomes)
    if accepted and a.dual:tot['truly_independent_dual']+=1
    return {'accepted':accepted,'proof':outcomes,'typed_ast_sha256':hashlib.sha256(inv.encode()).hexdigest()}
   for i,rec in enumerate(item.get('learner',[])):
    for key,dst,method in [('trained_invariant','trained','learned'),('untrained_invariant','initialization_only','untrained')]:
     inv=rec[key];row[dst].append({'seed':i,**verify(inv)})
   for i,rec in enumerate(item.get('exact_same_samples',[])):
    row['exact_rational'].append({'basis':i,**verify(rec['invariant'])})
   # mutations on original Pre/Goal: SAT expected for non-vacuous benchmark; do not exclude if one invalid.
   for k,c in [('false_init',pre),('true_post',f'(not {post})')]:
    sc=hdr+'(assert '+c+')\n(check-sat)\n'
    zr=z.run(sc)
    if zr=='sat':tot['mutant_false_sat' if k=='false_init' else 'mutant_true_sat']+=1
    row[k]={'Z3':zr,'sha256':hashlib.sha256(sc.encode()).hexdigest()}
   row['status']='CHECKED';tot['cases']+=1
  except Exception as ex:
   row['status']='ABSTAIN_OR_FAILED';row['case_errors'].append(type(ex).__name__+':'+str(ex)[:160])
  r.append(row);print('INDEPENDENT_DUAL_CASE',reg['name'],row['status'],'trained',sum(x['accepted'] for x in row['trained']),'control',sum(x['accepted'] for x in row['initialization_only']),'exact',sum(x['accepted'] for x in row['exact_rational']),flush=True)
 report={'schema':'NEUMANN.Q3.source9.frozen.adam_vs_exact_vs_nograd.independent_original_vc.v1','source_manifest_sha256':hashlib.sha256(pathlib.Path(a.manifest).read_bytes()).hexdigest(),'raw_first_receipt_sha256':hashlib.sha256(pathlib.Path(a.receipt).read_bytes()).hexdigest(),'backend':'dual_z3_cvc5' if a.dual else 'z3_only','counts':tot,'cases':r,'global_Q3_Q4_Q6':'OPEN'}
 out=pathlib.Path(a.out);out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print('DUTIES',json.dumps(tot),flush=True)
if __name__=='__main__':main()