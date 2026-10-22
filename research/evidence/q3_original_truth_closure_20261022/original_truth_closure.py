#!/usr/bin/env python3
"""Original source SHA-bound, exact safety-truth closure.

Three non-learned, human-proposed inductive invariants on published SyGuS
originals, and one independently reachable unsafe trace. This is strictly
posthoc, not a trained invention/first-blind candidate study.
"""
import argparse, ctypes, hashlib, json, pathlib, re, subprocess, shutil, time

EXPECTED={
 'ex23.sl':('ada3eae4e8e9f4368c2a3ca0d2ecb900624dc7f9',559,
  '(and (<= 0 y) (<= y 127) (<= 0 c) (<= c 36) (= z (+ (* 36 y) c)))',
  'comp/2017/Inv_Track/ex23.sl'),
 'fib_13.sl':('b583a100b7c5a4b9b25a22c4c881b1cd90e2e3ee',586,
  '(and (=> (= t 0) (= k 0)) (=> (not (= t 0)) (= j (+ (* 2 k) 2))))',
  'comp/2019/Inv_Track/From2018/fib_13.sl'),
 'fib_11.sl':('5fd3d40e22d7d724eb1e9002a1c2a5fe1f46bb3f',589,
  '(and (> x 0) (<= 0 i) (<= i x) (= j (* 2 i)))',
  'comp/2019/Inv_Track/From2018/fib_11.sl'),
 'fib_07.sl':('94386ca5ecad64a5267166d577c6bb690a55cf86',766,
  None,'comp/2019/Inv_Track/From2018/fib_07.sl')}
PIN='13c8deb68a873635879c9a69bc78caebd340f646'

def balanced(s,i):
 d=0
 for j in range(i,len(s)):
  d+=(s[j]=='(')-(s[j]==')')
  if d==0:return s[i:j+1]
 raise ValueError('unbalanced')

def original(s):
 k=re.search(r'\(synth-inv\s+\S+\s+',s)
 if not k:raise ValueError('missing synth-inv')
 sig=balanced(s,k.end())
 names=re.findall(r'\(\s*([^\s()]+)\s+Int\s*\)',sig)
 defs=[balanced(s,k.start()) for k in re.finditer(r'\(define-fun\s+',s)]
 fn=[re.match(r'\(define-fun\s+(\S+)',d).group(1) for d in defs]
 if len(defs)!=3 or not names or len(set(names))!=len(names):raise ValueError('unsupported signature')
 return names,defs,fn

class Z3:
 def __init__(self):
  z=ctypes.CDLL('libz3.so.4');self.z=z
  z.Z3_mk_config.restype=ctypes.c_void_p
  z.Z3_mk_context.argtypes=[ctypes.c_void_p];z.Z3_mk_context.restype=ctypes.c_void_p
  z.Z3_eval_smtlib2_string.argtypes=[ctypes.c_void_p,ctypes.c_char_p];z.Z3_eval_smtlib2_string.restype=ctypes.c_char_p
  z.Z3_del_context.argtypes=[ctypes.c_void_p];z.Z3_del_config.argtypes=[ctypes.c_void_p]
 def query(self,s):
  z=self.z;cf=z.Z3_mk_config();ctx=z.Z3_mk_context(cf)
  try:
   ret=z.Z3_eval_smtlib2_string(ctx,s.encode())
   if not ret:raise RuntimeError('z3 null')
   raw=ret.decode().strip()
   status=next((x.strip() for x in raw.splitlines() if x.strip() in ('sat','unsat','unknown')),None)
   return status or 'ERROR'
  finally:z.Z3_del_context(ctx);z.Z3_del_config(cf)


def make_base(raw):
 names,defs,fn=original(raw)
 primed=[n+'!' for n in names]
 header='(set-logic LIA)\n'+ '\n'.join('(declare-const '+v+' Int)' for v in names+primed)+'\n'+'\n'.join(defs)+'\n'
 pre='('+fn[0]+' '+' '.join(names)+')'
 trans='('+fn[1]+' '+' '.join(names+primed)+')'
 post='('+fn[2]+' '+' '.join(names)+')'
 return header,names,pre,trans,post

def smt_int(x):return str(x) if x>=0 else '(- '+str(-x)+')'

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-dir',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--registry',type=pathlib.Path);p.add_argument('--cvc5',action='store_true');a=p.parse_args()
 a.out.mkdir(parents=True,exist_ok=True);(a.out/'queries').mkdir(exist_ok=True)
 z=Z3();summary=[];start=time.monotonic()
 reg=json.loads(a.registry.read_text()) if a.registry else None
 if reg:
  assert len(reg['cases'])==12 and len(set(x['name'] for x in reg['cases']))==12
  cases=[(x['name'],(x['sha'],x['size'],x['invariant'],x['path']),x['role'],x.get('original_registered_sha')) for x in reg['cases']]
 else:cases=[(n,v,('HUMAN_POSTHOC_INVARIANT' if v[2] else 'CONCRETE_REACHABLE_UNSAFE'),None) for n,v in EXPECTED.items()]
 for name,(expected_sha,expected_size,expr,path),role,registered_sha in cases:
  b=(a.source_dir/name).read_bytes();got=hashlib.sha1(('blob '+str(len(b))+'\0').encode()+b).hexdigest()
  if got!=expected_sha or len(b)!=expected_size:raise ValueError('ORIGINAL_IDENTITY_FAILURE '+name+': '+got)
  header,names,pre,trans,post=make_base(b.decode())
  row={'name':name,'path':path,'git_blob':got,'bytes':len(b),'original_version':PIN,'kind':'HUMAN_POSTHOC_SAFE_CANDIDATE' if expr else 'GROUNDED_REACHABLE_UNSAFE','query_status':{},'identity_ok':True,'role':role,'initial_registered_sha':registered_sha,'posthoc_sha_amendment':registered_sha is not None and registered_sha!=got}
  if expr:
   params=' '.join('('+n+' Int)' for n in names)
   h=header+'\n(define-fun I ('+params+') Bool '+expr+')\n'
   inv='(I '+' '.join(names)+')';invp='(I '+' '.join(n+'!' for n in names)+')'
   goal={'init':f'(and {pre} (not {inv}))','step':f'(and {inv} {trans} (not {invp}))','goal':f'(and {inv} (not {post}))',
        'false_negative_control':f'(and {pre} (not false))','true_negative_control':f'(and true (not {post}))'}
   row['invariant']=expr
  else:
   # Fully ground a concrete reachable model, with all four variables in both states.
   original_states=[dict(i=0,n=1,a=0,b=0),dict(i=1,n=0,a=1,b=2)]
   assign=['(= '+n+' '+smt_int(original_states[0][n])+')' for n in names]+['(= '+n+'! '+smt_int(original_states[1][n])+')' for n in names]
   h=header
   goal={'initial_witness':f'(and {pre} '+ ' '.join(assign)+')',
         'transition_witness':f'(and {pre} {trans} '+ ' '.join(assign)+')'}
   nextpost='('+re.match(r'\(([^\s()]+)',post).group(1)+' '+' '.join(n+'!' for n in names)+')'
   goal['unsafe_goal_witness']=f'(and {pre} {trans} (not {nextpost}) '+' '.join(assign)+')'
   row['states']=original_states
  for key,cond in goal.items():
   query=h+'(assert '+cond+')\n(check-sat)\n';fid=name.replace('.sl','')+'_'+key
   (a.out/'queries'/(fid+'.smt2')).write_text(query)
   expected=('sat' if (key in ('false_negative_control','true_negative_control') or expr is None) else 'unsat')
   t=time.monotonic();zresult=z.query(query)
   result={'expected':expected,'z3':zresult,'z3_ms':round((time.monotonic()-t)*1000,3),'sha256':hashlib.sha256(query.encode()).hexdigest()}
   if a.cvc5:
    if not shutil.which('cvc5'):raise RuntimeError('cvc5 executable missing')
    t=time.monotonic();c=subprocess.run(['cvc5','--lang','smt2','--tlimit=10000'],input=query,text=True,capture_output=True,timeout=18)
    lines=[x.strip() for x in c.stdout.splitlines()]
    result['cvc5']=next((x for x in lines if x in ('sat','unsat','unknown')),'ERROR')
    result['cvc5_ms']=round((time.monotonic()-t)*1000,3)
    result['stderr_tail']=c.stderr[-200:]
   if result['z3']!=expected or (a.cvc5 and result['cvc5']!=expected):raise AssertionError(f'{fid}: {result}')
   row['query_status'][key]=result
  row['status']=('DUAL_FULL_ORIGINAL_3VC_PASS' if a.cvc5 else 'Z3_FULL_ORIGINAL_3VC_PASS') if expr else ('DUAL_REACHABLE_UNSAFE_SAT_PASS' if a.cvc5 else 'Z3_REACHABLE_UNSAFE_SAT_PASS')
  summary.append(row)
  print('SOURCE_TRUTH_CLOSURE',name,row['status'],len(goal),flush=True)
 doc={'schema':'NEUMANN.q3.posthoc.original_exact_safety_truth.v1','upstream':PIN,'posthoc_manual_invariants':True,'not_learned':True,'registered_sha_repair':'fib_11 original cohort SHA was typo; verified correction has no firstblind privilege','manifest_sha256':hashlib.sha256(a.registry.read_bytes()).hexdigest() if a.registry else None,'cases':summary,'summary':{'authenticated':len(summary),'safe_full_three_vc':sum(bool(x['invariant']) if 'invariant' in x else False for x in summary),'unsafe_reachable_witness':sum(x['kind']=='GROUNDED_REACHABLE_UNSAFE' for x in summary),'queries':sum(len(x['query_status']) for x in summary),'backend_count':2 if a.cvc5 else 1},'wall_s':round(time.monotonic()-start,5)}
 (a.out/'RESULT.json').write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n')
 print('RECEIPT_SHA',hashlib.sha256((a.out/'RESULT.json').read_bytes()).hexdigest(),doc['summary'])
if __name__=='__main__':main()
