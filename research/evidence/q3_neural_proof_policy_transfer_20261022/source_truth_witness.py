#!/usr/bin/env python3
"""Independent source-semantic bounded UNSAFE discovery from official SyGuS original.

Checks TRUE original Pre, Trans, Post function definitions and source Git Blob,
constructs 0..D *reachable* source traces and replays each discovered concrete
witness in independent cvc5. No source-name routing, no human witness injection.
A bounded miss is UNKNOWN, NEVER a proof of unbounded SAFE.
"""
import argparse, ctypes, hashlib, json, pathlib, re, subprocess, time

def balanced(s,i):
 d=0
 for j in range(i,len(s)):
  d+=(s[j]=='(')-(s[j]==')')
  if d==0:return s[i:j+1]
 raise ValueError('unbalanced')

def original(s):
 k=re.search(r'\(synth-inv\s+\S+\s+',s)
 if not k:raise ValueError('no synth-inv')
 signature=balanced(s,k.end())
 names=re.findall(r'\(\s*([^\s()]+)\s+Int\s*\)',signature)
 f=[balanced(s,k.start()) for k in re.finditer(r'\(define-fun\s+',s)]
 if not names or len(f)!=3:raise ValueError('unsupported original')
 fn=[re.match(r'\(define-fun\s+(\S+)',x).group(1) for x in f]
 return names,f,fn

class Z3Lib:
 def __init__(self):
  z=ctypes.CDLL('libz3.so.4');self.z=z
  z.Z3_mk_config.restype=ctypes.c_void_p
  z.Z3_mk_context.argtypes=[ctypes.c_void_p];z.Z3_mk_context.restype=ctypes.c_void_p
  z.Z3_eval_smtlib2_string.argtypes=[ctypes.c_void_p,ctypes.c_char_p];z.Z3_eval_smtlib2_string.restype=ctypes.c_char_p
  z.Z3_del_context.argtypes=[ctypes.c_void_p];z.Z3_del_config.argtypes=[ctypes.c_void_p]
 def query(self,s):
  z=self.z;cf=z.Z3_mk_config();ctx=z.Z3_mk_context(cf)
  try:
   x=z.Z3_eval_smtlib2_string(ctx,s.encode())
   if not x:raise RuntimeError('Z3_null')
   return x.decode().strip()
  finally:z.Z3_del_context(ctx);z.Z3_del_config(cf)

def solver_status(out):
 vals=[x for x in out.splitlines() if x.strip() in ('sat','unsat','unknown')]
 return vals[0] if vals else 'UNSUPPORTED'

def int_literal(i):return str(i) if i>=0 else f'(- {-i})'

def certificate(row,raw,max_depth,z):
 names,defs,fns=original(raw.decode())
 allcases=[]
 for depth in range(max_depth+1):
  variables=[f'{n}__s{d}' for d in range(depth+1) for n in names]
  decl='\n'.join('(declare-const '+v+' Int)' for v in variables)
  states=[[f'{n}__s{d}' for n in names] for d in range(depth+1)]
  pre='('+fns[0]+' '+' '.join(states[0])+')'
  trans=['('+fns[1]+' '+' '.join(states[d]+states[d+1])+')' for d in range(depth)]
  post='('+fns[2]+' '+' '.join(states[-1])+')'
  conditions=[pre]+trans+['(not '+post+')']
  head='(set-logic LIA)\n'+decl+'\n'+'\n'.join(defs)+'\n'
  query=head+'\n'.join('(assert '+c+')' for c in conditions)+'\n(check-sat)\n'
  out=z.query(query)
  status=solver_status(out)
  probe=dict(depth=depth,z3=status,query_sha256=hashlib.sha256(query.encode()).hexdigest())
  row['probes'].append(probe)
  if status!='sat':continue
  detail=z.query(query+'(get-value ('+' '.join(variables)+'))\n')
  extracted={}
  for v in variables:
   match=re.search(r'\('+re.escape(v)+r'\s+(\(-\s*\d+\s*\)|-?\d+)\)',detail)
   if not match:raise RuntimeError('NO_CONCRETE_MODEL_FOR_'+v+' out='+detail[:250])
   w=match.group(1)
   extracted[v]=-int(re.search(r'\d+',w).group()) if w.startswith('(-') else int(w)
  grounded=query.replace('(check-sat)\n','')+'\n'.join('(assert (= '+v+' '+int_literal(extracted[v])+'))' for v in variables)+'\n(check-sat)\n'
  z_ground=z.query(grounded)
  if solver_status(z_ground)!='sat':raise RuntimeError('Z3_ground_witness_invalid')
  t=subprocess.run(['cvc5','--lang','smt2','--tlimit=6000'],input=grounded,text=True,capture_output=True,timeout=12)
  cstatus=solver_status(t.stdout)
  probe['ground_cvc5']=cstatus;probe['ground_z3']=solver_status(z_ground);probe['ground_sha256']=hashlib.sha256(grounded.encode()).hexdigest()
  if cstatus!='sat':raise RuntimeError('CVC5_ground_witness_not_sat_'+cstatus+'_'+t.stderr[-100:])
  probe['states']=[{n:extracted[f'{n}__s{d}'] for n in names} for d in range(depth+1)]
  row['status']='ORIGINAL_REACHABLE_UNSAFE_Z3_CVC5';row['depth']=depth;row['witness_sha256']=probe['ground_sha256'];return row
 row['status']='NOT_PROVEN_UNSAFE_WITHIN_BOUND';return row

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--manifest',type=pathlib.Path,required=True);ap.add_argument('--source-dir',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);ap.add_argument('--max-depth',type=int,default=2);args=ap.parse_args();assert 0<=args.max_depth<=4
 manifest=json.loads(args.manifest.read_text());assert len(manifest['cases'])>=1
 z=Z3Lib();rows=[];begin=time.monotonic()
 for case in manifest['cases']:
  row={'file':case['name'],'expected_gitblob':case['sha'],'source_path':case['path'],'status':'UNKNOWN','probes':[]}
  tic=time.monotonic()
  try:
   b=(args.source_dir/case['name']).read_bytes();gitsha=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
   if gitsha!=case['sha'] or len(b)!=case['size']:raise ValueError('SOURCE_IDENTITY_MISMATCH')
   row['actual_gitblob']=gitsha
   certificate(row,b,args.max_depth,z)
  except Exception as exc:row['status']='ABSTAIN_FAIL_CLOSED';row['error']=type(exc).__name__+':'+str(exc)[:300]
  row['wall_s']=round(time.monotonic()-tic,4);rows.append(row)
  print('SOURCE_TRUTH',row['file'],row['status'],row.get('depth'),row.get('error'),flush=True)
 summary={'n_original':len(rows),'verified_reachable_unsafe':sum(r['status']=='ORIGINAL_REACHABLE_UNSAFE_Z3_CVC5' for r in rows),'unsupported':sum(r['status']=='ABSTAIN_FAIL_CLOSED' for r in rows),'bounded_no_witness':sum(r['status']=='NOT_PROVEN_UNSAFE_WITHIN_BOUND' for r in rows)}
 out={'schema':'NEUMANN.Q3.original_source_reachable_unsafety_dual.v1','method':'original Pre/Trans/Post reachable 0,1,2 step counterexample with independently replayed ground assignment cvc5','maximum_depth':args.max_depth,'summary':summary,'cases':rows,'wall_s':round(time.monotonic()-begin,5)}
 args.out.parent.mkdir(exist_ok=True,parents=True);args.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print('ORIGINAL_TRUTH_SUMMARY',summary,'sha256',hashlib.sha256(args.out.read_bytes()).hexdigest())
if __name__=='__main__':main()
