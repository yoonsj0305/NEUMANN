#!/usr/bin/env python3
"""Independent second-backend, original source SMT-LIB replay of 8 published SyGuS programs.

Independent query authoring (separate from verify_real_sy_gus_representation_separation.py).
Only reports independent backend PASS when cvc5 is actually executed and agrees with Z3.
Human-supplied relational invariants and demonstration traces; no learning attribution.
"""
import argparse, ctypes, hashlib, json, pathlib, re, subprocess, time, urllib.request

PIN='13c8deb68a873635879c9a69bc78caebd340f646'
BASE=f'https://raw.githubusercontent.com/SyGuS-Org/benchmarks/{PIN}/'
# Source identities were preregistered in NEUMANN's historical 2026-10-21 corpus.
CASES={
'comp/2017/Inv_Track/formula22.sl': dict(sha='0c798b938140fb05e8d840b7e54ff47f07a1793b', names=['x1','x2','x3'], inv='(and (<= x1 x2) (or (>= x2 0) (<= (- x2 x3) 2)))',traces=[[[0,0,0],[1,1,0]]],cross=[1,0,0],from_=[(0,1),(0,0),(0,0)],bad=[[1,0,0]],post=True),
'comp/2017/Inv_Track/array.sl': dict(sha='56ed0ae1745b1603b116a490bf773ba29dcbf34b', names=['x','y','z'], inv='(not (and (>= x 5) (< z y)))',traces=[[[0,1,0],[1,0,0],[2,0,0],[3,0,0],[4,0,0],[5,0,0]]],cross=[5,1,0],from_=[(0,5),(0,0),(0,0)],bad=[[5,1,0]],post=True),
'comp/2017/Inv_Track/hola_countud.sl': dict(sha='5d7f07c0b5a35d119ebe2d59bd5f56e447c547bf',names=['x','y','n'],inv='(and (>= x 0) (= (+ x y) n))', traces=[[[1,0,1],[0,1,1]]],cross=[0,0,1],from_=[(0,1),(0,0),(0,0)],bad=[[0,0,1]],post=False),
'comp/2017/Inv_Track/sum1.sl': dict(sha='5fd2e4f7841aea6ebab96d30d394819b0d2b17d6',names=['i','n','sn'],inv='(and (= sn (- i 1)) (>= i 1) (or (= i 1) (<= i (+ n 1))))',traces=[[[1,1,0],[2,1,1]],[[1,0,0]]],cross=[2,0,1],from_=[(0,1),(1,0),(0,1)],bad=[[2,0,1]],post=False),
'comp/2019/Inv_Track/From2018/fib_15.sl': dict(sha='125d1f9a277e262df77bcbda1a77851841d563d3',names=['n','j','k'],inv='(and (> n 0) (>= j 0) (<= j n) (> (+ k j) n))',traces=[[[2,0,3],[2,1,2],[2,2,1]],[[1,0,2],[1,1,1]]],cross=[2,0,1],from_=[(0,0),(0,0),(1,1)],bad=[[2,0,1],[2,1,0],[2,2,-1]],post=False),
'comp/2019/Inv_Track/From2018/fib_41.sl': dict(sha='01d6662a6ce825939043683d96d33f07c3c32b04',names=['n','k','i','j'],inv='(and (>= n 0) (>= k 0) (= i j) (>= i 0) (<= i (+ n 1)))',traces=[[[1,0,0,0],[1,0,1,1],[1,0,2,2]]],cross=[1,0,2,0],from_=[(0,0),(0,0),(0,2),(0,0)],bad=[[1,0,2,0]],post=False),
'comp/2019/Inv_Track/From2018/fib_18.sl':dict(sha='03f37e87068ec2616c1747cf45860d7811c3ba99',names=['b','j','n','flag'],inv='(and (> n 0) (>= b 0) (<= b n) (=> (= flag 1) (= j b)))',traces=[[[0,0,2,1],[1,1,2,1],[2,2,2,1]]],cross=[2,0,2,1],from_=[(0,2),(0,0),(0,0),(0,0)],bad=[[2,0,2,1]],post=False),
'comp/2019/Inv_Track/From2018/jmbl_tacas.sl':dict(sha='07da5f3887401f7f778cf6cea87cea12a6fe1f83',names=['i','j','x','y'],inv='(= (- x y) (- i j))',traces=[[[0,0,0,0]],[[0,1,0,1]]],cross=[0,0,0,1],from_=[(0,0),(0,0),(0,0),(1,0)],bad=[[0,0,0,1]],post=False),
}
def git_blob(data):return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
def split_forms(src):
 out=[]
 for m in re.finditer(r'\(define-fun\s+',src):
  depth=0;end=None
  for i in range(m.start(),len(src)):
   depth+=(src[i]=='(')-(src[i]==')')
   if depth==0: end=i+1;break
  if end is None:raise ValueError('truncated definition')
  out.append(src[m.start():end])
 if len(out)!=3:raise ValueError('expected 3 source formula definitions')
 return out, [re.search(r'\(define-fun\s+(\S+)',s).group(1) for s in out]
def number(x):return str(x) if x>=0 else f'(- {-x})'
def ground(fn,values):return f'({fn} '+ ' '.join(map(number,values))+')'
class LibZ3:
 def __init__(self):
  z=ctypes.CDLL('libz3.so.4');self.z=z
  z.Z3_mk_config.restype=ctypes.c_void_p
  z.Z3_mk_context.argtypes=[ctypes.c_void_p];z.Z3_mk_context.restype=ctypes.c_void_p
  z.Z3_eval_smtlib2_string.argtypes=[ctypes.c_void_p,ctypes.c_char_p];z.Z3_eval_smtlib2_string.restype=ctypes.c_char_p
  z.Z3_del_context.argtypes=[ctypes.c_void_p];z.Z3_del_config.argtypes=[ctypes.c_void_p]
 def run(self,query):
  z=self.z;cfg=z.Z3_mk_config();ctx=z.Z3_mk_context(cfg)
  try:r=z.Z3_eval_smtlib2_string(ctx,query.encode()).decode().strip()
  finally:z.Z3_del_context(ctx);z.Z3_del_config(cfg)
  return r

def main():
 arg=argparse.ArgumentParser()
 arg.add_argument('--source-dir',type=pathlib.Path,default=None)
 arg.add_argument('--backend',choices=['z3','dual'],default='dual')
 arg.add_argument('--out',type=pathlib.Path,required=True)
 a=arg.parse_args();z=LibZ3();rows=[];counts={'z3':0,'cvc5':0,'unsat_vc':0,'unary_witnesses':0,'post_only_sufficient':0,'rejected_mutants':0}
 def require(q,expected,role):
  digest=hashlib.sha256(q.encode()).hexdigest();beg=time.perf_counter_ns()
  r=z.run(q);zw=(time.perf_counter_ns()-beg)/1e6;counts['z3']+=1
  if r!=expected:raise AssertionError(f'Z3 {role} expected={expected} actual={r} q={digest}')
  entry={'sha256':digest,'role':role,'expected':expected,'Z3':r,'Z3_wall_ms':zw}
  if a.backend=='dual':
   beg=time.perf_counter_ns()
   p=subprocess.run(['cvc5','--lang','smt2','--tlimit=5000'],input=q,text=True,capture_output=True,timeout=10)
   lines=[s.strip() for s in p.stdout.splitlines() if s.strip() in ('sat','unsat','unknown')]
   cv=lines[-1] if lines else f'EXIT_{p.returncode}:{p.stderr[-500:]}'
   if cv!=expected:raise AssertionError(f'cvc5 {role} expected={expected} actual={cv} q={digest}')
   entry.update(cvc5=cv,cvc5_wall_ms=(time.perf_counter_ns()-beg)/1e6);counts['cvc5']+=1
  return entry
 for path,c in CASES.items():
  local=(a.source_dir/pathlib.Path(path).name) if a.source_dir else None
  raw=local.read_bytes() if local else urllib.request.urlopen(BASE+path,timeout=30).read()
  if git_blob(raw)!=c['sha']:raise AssertionError(f'Original immutable source identity mismatch {path}')
  original=raw.decode();forms,(pre,trans,post)=split_forms(original);v=c['names'];vp=[x+'!' for x in v]
  decl='\n'.join(f'(declare-const {s} Int)' for s in v+vp)
  src='(set-logic LIA)\n'+decl+'\n'+'\n'.join(forms)+'\n'
  pre_v=f'({pre} '+ ' '.join(v)+')';tr_v=f'({trans} '+ ' '.join(v+vp)+')';post_v=f'({post} '+ ' '.join(v)+')'
  def query(condition,inv='',what=''):
   return require(src+inv+'\n(assert '+condition+')\n(check-sat)\n', 'unsat' if what=='UNSAT' else 'sat',what)
  invariant='(define-fun I ('+' '.join(f'({x} Int)' for x in v)+') Bool '+c['inv']+')'
  def conjunct(k):return '(I '+' '.join(k)+')'
  bads={
   'INIT':'(and '+pre_v+' (not '+conjunct(v)+'))',
   'STEP':'(and '+conjunct(v)+' '+tr_v+' (not '+conjunct(vp)+'))',
   'GOAL':'(and '+conjunct(v)+' (not '+post_v+'))'}
  per={'path':path,'sha1':c['sha'],'raw_sha256':hashlib.sha256(raw).hexdigest(),'invariant_human':c['inv'],'proofs':{},'trace_checks':[],'coordinate_provenance':[]}
  for name,cond in bads.items():
   per['proofs'][name]=query(cond,invariant,'UNSAT');counts['unsat_vc']+=1
  # Distinct negative controls, using identical original body.
  p1=query('(and '+pre_v+' (not false))','', 'SAT')
  p2=query('(not '+post_v+')','', 'SAT')
  per['mutant_FALSE_init']=p1;per['mutant_TRUE_goal']=p2;counts['rejected_mutants']+=2
  now_post='(define-fun I ('+' '.join(f'({x} Int)' for x in v)+') Bool '+post_v+')'
  post_consec=src+now_post+'\n(assert '+bads['STEP']+')\n(check-sat)\n'
  per['post_only_consecution']=require(post_consec,'unsat' if c['post'] else 'sat','post-only')
  counts['post_only_sufficient']+=int(c['post'])
  # Constructive finite original-reachable traces + cartesian recombination witness.
  for t in c['traces']:
   per['trace_checks'].append(query(ground(pre,t[0]),what='SAT'))
   for u,w in zip(t,t[1:]):per['trace_checks'].append(query(ground(trans,u+w),what='SAT'))
  for j,(ti,si) in enumerate(c['from_']):
   value=c['traces'][ti][si][j]
   if value!=c['cross'][j]:raise AssertionError('spurious coordinate not reachable')
   per['coordinate_provenance'].append({'coord':v[j],'source_trace':ti,'state_index':si,'integer':value})
  if c['cross']!=c['bad'][0]:raise AssertionError('invalid recombination start')
  for u,w in zip(c['bad'],c['bad'][1:]):per['trace_checks'].append(query(ground(trans,u+w),what='SAT'))
  per['spurious_violates_post']=query('(not '+ground(post,c['bad'][-1])+')',what='SAT')
  per['spurious_correct_post_unsat']=query(ground(post,c['bad'][-1]),what='UNSAT')
  counts['unary_witnesses']+=1
  rows.append(per)
  print(path, 'source_SHA_PASS 3VC_PASS no_unary_conj PASS',flush=True)
 status=('DUAL_Z3_CVC5_ORIGINAL_FULL_INDUCTION_AND_REPRESENTATION_BARRIER_PASS' if a.backend=='dual' else 'Z3_ONLY_REPLAY_PASS')
 r={'schema':'neumann.q3.real8_independent_second_backend.v1','status':status,'benchmark_commit':PIN,'scope':'8 previously opened authentic originals; human-supplied invariant and traces; no learned novelty','counts':counts,'backend':a.backend,'global_Q3_Q4_Q6':'OPEN','cases':rows}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
 print('DECISION',status,counts,flush=True);print('RECEIPT_SHA256',hashlib.sha256(a.out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()