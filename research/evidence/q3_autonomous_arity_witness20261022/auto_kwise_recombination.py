#!/usr/bin/env python3
"""Bounded, source-only automatic interaction-arity impossibility witness synthesizer.
Does not receive fake states, reachable projection witnesses or winning invariants.
Sound k-ary conjunction lower bound iff every generated witness/step is checked.
Completeness is bounded by exploration depth, value box, and unsafe lookahead.
"""
import argparse, ctypes, hashlib, itertools, json, pathlib, re, time, subprocess, sys

UPSTREAM='SyGuS-Org/benchmarks@13c8deb68a873635879c9a69bc78caebd340f646'
SOURCE_ID={
 'hola_countud.sl':'5d7f07c0b5a35d119ebe2d59bd5f56e447c547bf',
 'fib_15.sl':'125d1f9a277e262df77bcbda1a77851841d563d3',
 'fib_18.sl':'03f37e87068ec2616c1747cf45860d7811c3ba99',
 'jmbl_tacas.sl':'07da5f3887401f7f778cf6cea87cea12a6fe1f83',
}
class Z3:
 def __init__(self):
  z=self.z=ctypes.CDLL('libz3.so.4')
  z.Z3_mk_config.restype=ctypes.c_void_p
  z.Z3_mk_context.argtypes=[ctypes.c_void_p];z.Z3_mk_context.restype=ctypes.c_void_p
  z.Z3_eval_smtlib2_string.argtypes=[ctypes.c_void_p,ctypes.c_char_p];z.Z3_eval_smtlib2_string.restype=ctypes.c_char_p
  z.Z3_del_context.argtypes=[ctypes.c_void_p];z.Z3_del_config.argtypes=[ctypes.c_void_p]
 def run(self,txt):
  z=self.z;c=z.Z3_mk_config();ctx=z.Z3_mk_context(c)
  try: v=z.Z3_eval_smtlib2_string(ctx,txt.encode()).decode()
  finally:z.Z3_del_context(ctx);z.Z3_del_config(c)
  lines=v.strip().splitlines()
  if not lines or lines[0] not in ('sat','unsat'):raise RuntimeError('BAD_Z3_RETURN '+repr(v[:200]))
  if lines[0]=='unsat':return 'unsat',''
  if 'error' in v or 'unknown' in v: raise RuntimeError('Z3_SMT_FAILURE '+v[:500])
  return lines[0], '\n'.join(lines[1:]).strip()

def parse_original(raw):
 state=re.search(r'\(synth-inv\s+\S+\s+\(\((\S+)\s+Int\)',raw)
 if not state:raise ValueError('NO_STATE_DECL')
 start=raw.index('(synth-inv');stop=raw.index('(declare-primed-var',start)
 decl=raw[start:stop]
 vars_=re.findall(r'\(([^\s()]+)\s+Int\)',decl)
 forms=[]
 for m in re.finditer(r'\(define-fun\s+',raw):
  i=m.start();d=0;end=None
  for j in range(i,len(raw)):
   if raw[j]=='(':d+=1
   elif raw[j]==')':
    d-=1
    if d==0:end=j+1;break
  if end is None:raise ValueError('UNBALANCED')
  forms.append(raw[i:end])
 if len(forms)!=3:raise ValueError('PRE_TRANS_POST_NOT_THREE')
 fun=[re.search(r'\(define-fun\s+(\S+)',f).group(1) for f in forms]
 return vars_,forms,fun

def sname(kind,trace,step,coordinate):return f'{kind}{trace}_{step}_{coordinate}'
def smt_num(x):return str(x) if x>=0 else f'(- {-x})'
def call(name,state):return '('+name+' '+' '.join(state)+')'
def bounds(x,low,high):return '(and (<= '+str(low)+' '+x+') (<= '+x+' '+str(high)+'))'
def smt_eq(a,b):return '(= '+a+' '+b+')'
def conj(items):return '(and '+' '.join(items)+')' if items else 'true'
def parse_value(text,names):
 # Z3's get-value output: ((B_0_0 1)\n (P_0_0_0 (- 2)))
 pairs=re.findall(r'\(('+ '|'.join(re.escape(x) for x in sorted(names,key=len,reverse=True))+r')\s+(\(-\s+\d+\)|-?\d+)\)',text)
 d={k:-int(v[3:-1].strip()) if v.startswith('(- ') else int(v) for k,v in pairs}
 if len(d)!=len(names):raise ValueError('MODEL_PARSING_INCOMPLETE '+str(len(d))+' of '+str(len(names))+' model='+text[:300])
 return d

def source_head(vars_,forms):
 # Fully original Pre,Trans,Post, only fresh symbolic constants introduced.
 return '(set-logic LIA)\n'+'\n'.join(forms)+'\n'

def make_candidate(vars_,forms,fun,k,D,L,lo,hi):
 n=len(vars_);S=list(itertools.combinations(range(n),k))
 decl=[];constraints=[];get=[]
 b=[sname('B',0,t,i) for t in range(L+1) for i in range(n)]
 bsteps=[[sname('B',0,t,i) for i in range(n)] for t in range(L+1)]
 wsteps=[]
 for si,comb in enumerate(S):
  path=[[sname('W',si,t,i) for i in range(n)] for t in range(D+1)]
  wsteps.append(path)
  constraints.append(call(fun[0],path[0]))
  constraints.extend('('+ 'or '+call(fun[1],path[t]+path[t+1])+' '+conj([smt_eq(a,b) for a,b in zip(path[t],path[t+1])])+')' for t in range(D))
  constraints.extend(smt_eq(path[-1][i],bsteps[0][i]) for i in comb)
 for t in range(L):constraints.append(call(fun[1],bsteps[t]+bsteps[t+1]))
 constraints.append('(not '+call(fun[2],bsteps[-1])+')')
 for ar in bsteps+wsteps: pass
 states=bsteps+[st for path in wsteps for st in path]
 for ar in states:
  for x in ar: decl.append('(declare-const '+x+' Int)');get.append(x);constraints.append(bounds(x,lo,hi))
 text=source_head(vars_,forms)+'\n'.join(decl)+'\n(assert '+conj(constraints)+')\n(check-sat)\n(get-value ('+' '.join(get)+'))\n'
 return text,{'bad_states':bsteps,'witness_paths':wsteps,'projections':[list(u) for u in S]},get

def check_script(vars_,forms,fun,pre=None,step=None,postbad=None):
 vals=lambda ar:' '.join(smt_num(x) for x in ar)
 if pre is not None:expr='('+fun[0]+' '+vals(pre)+')'
 if step is not None:expr='('+fun[1]+' '+vals(step[0])+' '+vals(step[1])+')'
 if postbad is not None:expr='(not ('+fun[2]+' '+vals(postbad)+'))'
 return source_head(vars_,forms)+'(assert '+expr+')\n(check-sat)\n'

def main():
 a=argparse.ArgumentParser()
 a.add_argument('--source-dir',default='sources');a.add_argument('--out',default='RESULT.json');a.add_argument('--smt-out',default='smt')
 a.add_argument('--cvc5',action='store_true');a.add_argument('--max-witness-depth',type=int,default=3)
 a.add_argument('--max-unsafe-depth',type=int,default=3);a.add_argument('--lower',type=int,default=-4);a.add_argument('--upper',type=int,default=6)
 args=a.parse_args();outdir=pathlib.Path(args.smt_out);outdir.mkdir(parents=True,exist_ok=True)
 zz=Z3();t0=time.perf_counter();results={};totals={'sat_verified_queries':0,'generator_sat_queries':0,'generator_unsat_queries':0,'cvc5_replays':0};queries=[]
 def certify(sourceid,label,smt):
  res,rest=zz.run(smt)
  if res!='sat':raise AssertionError(('EVIDENCE_INVALID',sourceid,label,res))
  path=outdir/(sourceid.replace('.sl','')+'_'+label+'.smt2');path.write_text(smt)
  if args.cvc5:
   cp=subprocess.run(['cvc5','--lang','smt2',str(path)],capture_output=True,text=True,timeout=25)
   if cp.returncode or cp.stdout.strip()!='sat':raise AssertionError(('INDEPENDENT_CVC5_FAILED',label,cp.stdout,cp.stderr))
   totals['cvc5_replays']+=1
  totals['sat_verified_queries']+=1
  queries.append({'source':sourceid,'label':label,'sha256':hashlib.sha256(smt.encode()).hexdigest(),'z3':'sat','cvc5':'sat' if args.cvc5 else 'NOT_RUN'})
 for filename,expected in SOURCE_ID.items():
  data=(pathlib.Path(args.source_dir)/filename).read_bytes();h=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
  if h!=expected:raise ValueError('SOURCE_SHA_MISMATCH '+filename)
  vars_,forms,fun=parse_original(data.decode());n=len(vars_);found={};count=0
  for k in range(1,n):
   match=None
   # prefer shortest witness and bad-path, deterministic source-agnostic schedule
   for D in range(args.max_witness_depth+1):
    for L in range(args.max_unsafe_depth+1):
     src,loc,get=make_candidate(vars_,forms,fun,k,D,L,args.lower,args.upper)
     status,_=zz.run(src.split('\n(get-value (')[0]+'\n');count+=1
     if status=='unsat':totals['generator_unsat_queries']+=1;continue
     totals['generator_sat_queries']+=1
     status2,model=zz.run(src)
     if status2!='sat':raise AssertionError('NONDETERMINISTIC_SOLVER')
     dat=parse_value(model,get)
     def read(row):return [dat[x] for x in row]
     bad=[read(z) for z in loc['bad_states']]
     witnesses=[]
     for ix,steps in enumerate(loc['witness_paths']):
      path=[read(z) for z in steps]
      # remove virtual stutters: they are not original source transitions
      trail=[path[0]]
      for v in path[1:]:
       if v!=trail[-1]:trail.append(v)
      witnesses.append({'coordinates':loc['projections'][ix],'states':trail,'original_full_trace':path})
     # Confirm every concrete original source Pre and real transition, not just trust model.
     for i,w in enumerate(witnesses):
      states=w['states'];certify(filename,f'k{k}_pre_proj{i}',check_script(vars_,forms,fun,pre=states[0]))
      for t,(x,y) in enumerate(zip(states,states[1:])):
       certify(filename,f'k{k}_step_proj{i}_{t}',check_script(vars_,forms,fun,step=(x,y)))
      if tuple(states[-1][j] for j in w['coordinates'])!=tuple(bad[0][j] for j in w['coordinates']):raise AssertionError('PROJECTION_MISMATCH')
     for i,(x,y) in enumerate(zip(bad,bad[1:])):certify(filename,f'k{k}_bad_step_{i}',check_script(vars_,forms,fun,step=(x,y)))
     certify(filename,f'k{k}_bad_post',check_script(vars_,forms,fun,postbad=bad[-1]))
     match={'k':k,'witness_depth_bound':D,'bad_path_depth':L,'spurious_glued_state':bad[0],
       'original_unsafe_path_from_glue':bad,'projection_witnesses':witnesses,'source_sha':h,
       'mathematical_theorem':'No safety-inductive invariant of form conjunction of any arbitrary predicates with support <= k source coordinates and no auxiliary state can exist. This statement holds globally despite bounded computation because each concrete witness is authentic.'}
     break
    if match:break
   found[str(k)]=match
   print(filename,'arity',k,'CERTIFIED' if match else 'NOT_FOUND_WITH_BOUNDS','queries',count,flush=True)
  highest=max((int(k) for k,v in found.items() if v),default=0)
  results[filename]={'original_sha':h,'variables':vars_,'search_witness_bound':args.max_witness_depth,
   'search_bad_depth_bound':args.max_unsafe_depth,'search_integer_interval':[args.lower,args.upper],
   'witnesses_by_k':found,'highest_k_lower_bound_certified':highest,'necessary_support_at_least':highest+1,
   'not_proven':'NOT_FOUND means unknown, never impossibility of witnesses or representability. This run performs no independent upper-bound proof and does not train neural models.'}
 result={'schema':'NEUMANN.Q3.AUTOMATIC_KWISE_WITNESS_DISCOVERY.v1','source_upstream':UPSTREAM,
         'evidence':'SOURCE_ONLY search without user-provided fake state, trace or invariant; every asserted concrete Pre/Trans/NotPost independently rechecked',
         'original_count':len(results),'certified':results,'totals':totals,
         'query_count_verified':len(queries),'verifier_receipt':queries,
         'cvc5_run':args.cvc5,'wall_time_s':round(time.perf_counter()-t0,4),
         'global_Q3_learned_specific':'OPEN','complete_search':False}
 path=pathlib.Path(args.out);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print('TOTALS',json.dumps({k:v for k,v in result.items() if k not in ('certified','verifier_receipt')},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
