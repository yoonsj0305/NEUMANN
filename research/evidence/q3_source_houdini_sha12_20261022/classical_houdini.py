#!/usr/bin/env python3
"""Source-only, zero-learn, generic predicate generation + exact Z3 Houdini.

No prewritten invariant candidates allowed. Prior opened 8 SyGuS originals are a
POSTHOC development cohort. Requires full source Pre/Trans/Post original 3VC.
No uniqueness/novelty/first-blind claim; compare stronger source-only SPACER later.
"""
import itertools, re, ctypes, pathlib, json, time, hashlib, argparse, math
ROOT=pathlib.Path('/mnt/data/neumann_external_relational_gate_20261022/sources')
class LibZ3:
 def __init__(self):
  z=ctypes.CDLL('libz3.so.4');self.z=z
  z.Z3_mk_config.restype=ctypes.c_void_p
  z.Z3_mk_context.argtypes=[ctypes.c_void_p];z.Z3_mk_context.restype=ctypes.c_void_p
  z.Z3_eval_smtlib2_string.argtypes=[ctypes.c_void_p,ctypes.c_char_p];z.Z3_eval_smtlib2_string.restype=ctypes.c_char_p
  z.Z3_del_context.argtypes=[ctypes.c_void_p];z.Z3_del_config.argtypes=[ctypes.c_void_p]
 def run(self, script):
  z=self.z;cfg=z.Z3_mk_config();ctx=z.Z3_mk_context(cfg)
  try:
   raw=z.Z3_eval_smtlib2_string(ctx,script.encode())
   if not raw: raise RuntimeError('Z3 returned null')
   result=raw.decode().strip().splitlines()
  finally:z.Z3_del_context(ctx);z.Z3_del_config(cfg)
  return result
z=LibZ3()
def balanced(src, i):
 assert src[i]=='('
 n=0
 for j in range(i,len(src)):
  n+=(src[j]=='(')-(src[j]==')')
  if n==0:return src[i:j+1]
 raise ValueError('unbalanced')
def parse(src):
 synth=re.search(r'\(synth-inv\s+\S+\s+',src)
 sig=balanced(src,synth.end())
 names=re.findall(r'\(\s*([^\s()]+)\s+Int\s*\)',sig)
 fs=[balanced(src,m.start()) for m in re.finditer(r'\(define-fun\s+',src)]
 if len(fs)!=3:raise ValueError('define-fun count != 3')
 fns=[re.search(r'\(define-fun\s+(\S+)',f).group(1) for f in fs]
 assert names and len(names)<=5
 return names,fs,fns
def plus(xs):
 if len(xs)==1:return xs[0]
 return '(+ '+' '.join(xs)+')'
def term(vals,names):
 s=[]
 for c,n in zip(vals,names):
  if c==1:s.append(n)
  if c==-1:s.append('(- '+n+')')
 return plus(s)
def pred_pool(names,body,max_support=4,include_guards=True):
 n=len(names); seen=set();d={}
 def add(s,tag):
  if s not in seen:
   seen.add(s);d[s]=tag
 # All homogeneous affine features support up to 4 interacting variables.
 for c in itertools.product((-1,0,1),repeat=n):
  if all(v==0 for v in c):continue
  if next(v for v in c if v)!=1:continue
  if sum(v!=0 for v in c)>max_support:continue
  t=term(c,names)
  for bound in (-2,-1,0,1,2):
   for op in ('=', '<=', '>='):
    add(f'({op} {t} {bound if bound>=0 else f"(- {-bound})"})','LINEAR')
 # Predicate atoms from post, generally complex, use full Post separately.
 # Specific guarded equalities are driven by all source syntactic '(= var literal)'
 guards=set()
 for x,val in re.findall(r'\(=\s+([\w!]+)\s+(-?\d+)\)',body):
  if x in names and -1<=int(val)<=2:guards.add((x,int(val)))
 for g,val in sorted(guards) if include_guards else []:
  for a,b in itertools.combinations([x for x in names if x!=g],2):
   for e in (f'(= {a} {b})',f'(= {a} (- {b}))',f'(<= {a} {b})',f'(>= {a} {b})'):
    add(f'(=> (= {g} {val if val>=0 else f"(- {-val})"}) {e})','GUARDED')
 # Source post itself gets independent chance to be retained if inductive in conjunction.
 return d

def check_batch(src,clauses):
 # Handles many batched requests with original full formula declared once
 prog=[src,'(set-option :timeout 2000)']
 for x in clauses:prog.extend(['(push 1)','(assert '+x+')','(check-sat)','(pop 1)'])
 outs=z.run('\n'.join(prog))
 results=[i.strip() for i in outs if i.strip() in ('unsat','sat','unknown')]
 if len(results)!=len(clauses):raise RuntimeError('Batch status count mismatch '+str((len(results),len(clauses),outs[:6])))
 return results

def conj(parts):return '(and '+' '.join(parts)+')' if parts else 'true'
def ren(expr,names):
 # SMT lexical tokens: replace originals with primed names, preserve Post/Trans function symbols
 return re.sub(r'(?<![\w!])('+'|'.join(map(re.escape,names))+r')(?![\w!])',lambda m:m.group(1)+'!',expr)

def main():
 pa=argparse.ArgumentParser();pa.add_argument('--out',default='/mnt/data/NEUMANN_Q3_AUTO_HOUDINI_FIRST_RECEIPT_20261022.json');pa.add_argument('--input',type=pathlib.Path,default=ROOT);pa.add_argument('--manifest',type=pathlib.Path,default=None);pa.add_argument('--max-support',type=int,default=4);pa.add_argument('--no-guards',action='store_true');args=pa.parse_args()
 rows=[];allstart=time.monotonic()
 entries=json.loads(args.manifest.read_text())['cases'] if args.manifest else [{'name':p.name,'sha':None,'path':str(p)} for p in sorted(args.input.glob('*.sl'))]
 for entry in entries:
  path=args.input/entry['name'];start=time.monotonic();row={'file':path.name,'original_git_sha1_expected':entry.get('sha'),'original_path':entry['path'],'source_algorithm':'UNTRAINED_SOURCE_ONLY_FINITE_AFFINE_GUARDED_HOUDINI','calls':0}
  try:
   raw=path.read_bytes();text=raw.decode()
   if entry.get('sha'):
    gitsha=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
    if gitsha!=entry['sha']:raise RuntimeError('ORIGINAL_GIT_BLOB_MISMATCH')
   names,forms,fns=parse(text)
   decls='\n'.join(f'(declare-const {v} Int)\n(declare-const {v}! Int)' for v in names)
   source='(set-logic LIA)\n'+decls+'\n'+'\n'.join(forms)+'\n'
   pre='('+fns[0]+' '+' '.join(names)+')';trans='('+fns[1]+' '+' '.join(names+[v+'!' for v in names])+')';post='('+fns[2]+' '+' '.join(names)+')'
   postp='('+fns[2]+' '+' '.join([v+'!' for v in names])+')'
   row.update({'original_sha256':hashlib.sha256(raw).hexdigest(),'vars':names})
   # This is a genuine source-only exact Post check; when suffices, fast-path.
   obligations=[f'(and {pre} (not {post}))',f'(and {post} {trans} (not {postp}))']
   posts=check_batch(source,obligations);row['calls']+=len(posts)
   row['post_only']=posts
   if posts==['unsat','unsat']:
    cand=[post];row['initial_pool']=0;row['after_init']=0;row['houdini_rounds']=0
   else:
    pool=pred_pool(names,forms[0]+forms[1],max_support=args.max_support,include_guards=not args.no_guards);pool[post]='POST'
    candidate=list(pool)
    init=check_batch(source,[f'(and {pre} (not {c}))' for c in candidate]);row['calls']+=len(candidate)
    keep=[x for x,y in zip(candidate,init) if y=='unsat']
    row['initial_pool']=len(candidate);row['after_init']=len(keep);row['max_support']=args.max_support;row['guards']=not args.no_guards
    row['unknown_initial']=init.count('unknown')
    # classic exact Houdini fixed point
    loops=[]
    for r in range(8):
     premise=conj(keep)
     not_inductive=[f'(and {premise} {trans} (not {ren(c,names)}))' for c in keep]
     checks=check_batch(source,not_inductive);row['calls']+=len(checks)
     remove=[c for c,v in zip(keep,checks) if v!='unsat']
     loops.append({'round':r,'before':len(keep),'removed':len(remove),'unknown':checks.count('unknown')})
     keep=[c for c,v in zip(keep,checks) if v=='unsat']
     if not remove:break
    else:row['cap_reached']=True
    row['houdini_rounds']=len(loops);row['loops']=loops;cand=keep
   invariant=conj(cand)
   three=[f'(and {pre} (not {invariant}))',f'(and {invariant} {trans} (not {ren(invariant,names)}))',f'(and {invariant} (not {post}))']
   vc=check_batch(source,three);row['calls']+=3
   row['whole_source_original_3vc']=vc
   row['safe_certified']=all(v=='unsat' for v in vc)
   row['num_conjuncts']=len(cand);row['invariant']=invariant if row['safe_certified'] else None
   row['wall_s']=round(time.monotonic()-start,3)
  except Exception as e:
   row.update({'safe_certified':False,'abstain_reason':type(e).__name__+':'+str(e)[:180],'whole_source_original_3vc':None,'wall_s':round(time.monotonic()-start,3)})
  rows.append(row)
  print(path.name,row['safe_certified'],'candidates',row.get('initial_pool'),'remaining',row.get('num_conjuncts'),'rounds',row.get('houdini_rounds'),'3VC',row.get('whole_source_original_3vc'),'seconds',row['wall_s'],flush=True)
 report={'schema':'neumann.q3.source_only_classical_houdini_first_run.v1','status':'COMPLETE','scope':'posthoc previously opened real originals, no learned proposals, no model training, no manual candidate formula, no independent cvc5 in this run','cases':rows,'full_3vc_count':sum(r['safe_certified'] for r in rows),'number':len(rows),'total_wall_s':round(time.monotonic()-allstart,3),'global_Q3_Q4_Q6':'OPEN'}
 target=pathlib.Path(args.out);target.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print('SUMMARY',report['full_3vc_count'],'/',len(rows),'wall',report['total_wall_s'], 'sha256',hashlib.sha256(target.read_bytes()).hexdigest())
if __name__=='__main__':main()