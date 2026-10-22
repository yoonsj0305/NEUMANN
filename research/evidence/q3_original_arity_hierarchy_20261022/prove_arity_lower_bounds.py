#!/usr/bin/env python3
"""Exact k-wise projection amalgamation lower bounds on authentic SyGuS originals.

A nonadaptive, manually witnessed MATHEMATICAL expressivity theorem, not neural
learned discovery. All Pre, Trans and Post formulas are original, SHA validated.
Optional independently runs cvc5, never silently downgrades second-backend PASS.
"""
import argparse, ctypes, hashlib, itertools, json, pathlib, re, subprocess, time

UPSTREAM='SyGuS-Org/benchmarks@13c8deb68a873635879c9a69bc78caebd340f646'
CASES={
 'hola_countud.sl':dict(sha='5d7f07c0b5a35d119ebe2d59bd5f56e447c547bf', vars=['x','y','n'],k=2,
  invariant='(and (>= x 0) (= (+ x y) n))',bad=[0,0,1],bad_path=[[0,0,1]],
  proj={
    '0,1':[[0,0,0]],
    '0,2':[[1,0,1],[0,1,1]],
    '1,2':[[1,0,1]],
  }),
 'fib_15.sl':dict(sha='125d1f9a277e262df77bcbda1a77851841d563d3', vars=['n','j','k'],k=2,
  invariant='(and (> n 0) (>= j 0) (<= j n) (> (+ k j) n))',bad=[3,1,1],bad_path=[[3,1,1],[3,2,0],[3,3,-1]],
  proj={
    '0,1':[[3,0,4],[3,1,3]],
    '0,2':[[3,0,4],[3,1,3],[3,2,2],[3,3,1]],
    '1,2':[[1,0,2],[1,1,1]],
  }),
 'fib_18.sl':dict(sha='03f37e87068ec2616c1747cf45860d7811c3ba99', vars=['b','j','n','flag'],k=2,
  invariant='(and (> n 0) (>= b 0) (<= b n) (=> (= flag 1) (= j b)))',bad=[2,0,2,1],bad_path=[[2,0,2,1]],
  proj={
    '0,1':[[0,0,2,0],[1,0,2,0],[2,0,2,0]],
    '0,2':[[0,0,2,0],[1,0,2,0],[2,0,2,0]],
    '0,3':[[0,0,2,1],[1,1,2,1],[2,2,2,1]],
    '1,2':[[0,0,2,1]],
    '1,3':[[0,0,2,1]],
    '2,3':[[0,0,2,1]],
  }),
 'jmbl_tacas.sl':dict(sha='07da5f3887401f7f778cf6cea87cea12a6fe1f83', vars=['i','j','x','y'],k=3,
  invariant='(= (- x y) (- i j))',bad=[1,1,0,1],bad_path=[[1,1,0,1]],
  proj={
    '0,1,2':[[1,1,1,1],[1,1,0,0]],
    '0,1,3':[[1,1,1,1]],
    '0,2,3':[[1,2,1,2],[1,2,0,1]],
    '1,2,3':[[0,1,0,1]],
  }),
}

def original_forms(raw):
    out=[]
    for m in re.finditer(r'\(define-fun\s+',raw):
        start=m.start();dep=0;end=None
        for i in range(start,len(raw)):
            if raw[i]=='(':dep+=1
            elif raw[i]==')':
                dep-=1
                if dep==0:end=i+1;break
        if end is None:raise ValueError('UNBALANCED_SOURCE')
        out.append(raw[start:end])
    if len(out)!=3:raise ValueError('ORIGINAL_PRE_TRANS_POST_WRONG_COUNT')
    return out,[re.search(r'\(define-fun\s+(\S+)',f).group(1) for f in out]

def git_blob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def val(v):return str(v) if v>=0 else f'(- {-v})'
def func(name,values):return '('+name+' '+' '.join(map(val,values))+')'

class Z3:
    def __init__(self):
        z=self.z=ctypes.CDLL('libz3.so.4')
        z.Z3_mk_config.restype=ctypes.c_void_p
        z.Z3_mk_context.argtypes=[ctypes.c_void_p];z.Z3_mk_context.restype=ctypes.c_void_p
        z.Z3_eval_smtlib2_string.argtypes=[ctypes.c_void_p,ctypes.c_char_p];z.Z3_eval_smtlib2_string.restype=ctypes.c_char_p
        z.Z3_del_context.argtypes=[ctypes.c_void_p];z.Z3_del_config.argtypes=[ctypes.c_void_p]
    def run(self,script):
        z=self.z;cfg=z.Z3_mk_config();ctx=z.Z3_mk_context(cfg)
        try:r=z.Z3_eval_smtlib2_string(ctx,script.encode()).decode().strip()
        finally:z.Z3_del_context(ctx);z.Z3_del_config(cfg)
        if r not in ('sat','unsat'):raise RuntimeError(f'Z3_{r}')
        return r


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source-dir',default=str(pathlib.Path(__file__).resolve().parent/'sources'))
    ap.add_argument('--out',default=str(pathlib.Path(__file__).resolve().parent/'result.json'))
    ap.add_argument('--queries-dir',default=str(pathlib.Path(__file__).resolve().parent/'smt2'))
    ap.add_argument('--cvc5',action='store_true')
    a=ap.parse_args();base=pathlib.Path(a.source_dir);query_dir=pathlib.Path(a.queries_dir);query_dir.mkdir(parents=True,exist_ok=True)
    z3=Z3();log={};queries=0;counts={'sat':0,'unsat':0};t0=time.perf_counter()
    for filename,c in CASES.items():
        data=(base/filename).read_bytes();h=git_blob(data)
        if h!=c['sha']:raise ValueError(f'SOURCE_SHA_MISMATCH {filename} {h}')
        forms,fn=original_forms(data.decode());vv=c['vars'];p,t,q=fn
        variables=vv+[v+'!' for v in vv]
        head='(set-logic LIA)\n'+'\n'.join('(declare-const '+v+' Int)' for v in variables)+'\n'+'\n'.join(forms)+'\n'
        rel='(define-fun INV ('+' '.join('('+v+' Int)' for v in vv)+') Bool '+c['invariant']+')\n'
        def check(label,phi,expected,inv=False):
            nonlocal queries
            queries+=1
            smt=head+(rel if inv else '')+'(assert '+phi+')\n(check-sat)\n'
            path=query_dir/f'{filename.replace(".sl","")}_{queries:03}_{label}.smt2'
            path.write_text(smt)
            got=z3.run(smt)
            if got!=expected:raise AssertionError((filename,label,expected,got))
            cv=None
            if a.cvc5:
                o=subprocess.run(['cvc5','--lang','smt2','--produce-models',str(path)],capture_output=True,text=True,timeout=20)
                if o.returncode:raise RuntimeError(f'cvc5 ERROR {filename} {label}: {o.stderr[:500]}')
                cv=o.stdout.strip()
                if cv!=expected:raise AssertionError((filename,label,'cvc5',expected,cv))
            counts[expected]+=1
            return {'z3':got,'cvc5':cv if a.cvc5 else 'NOT_RUN','sha256':hashlib.sha256(smt.encode()).hexdigest(),'script':path.name}
        k=c['k'];subsets=list(itertools.combinations(range(len(vv)),k));expected_keys={','.join(map(str,u)) for u in subsets}
        if set(c['proj'])!=expected_keys:raise AssertionError(f'MISSING_PROJECTION_WITNESS {filename}')
        if len(c['bad'])!=len(vv):raise AssertionError('SIZE')
        witnesses={}
        for ix,subset in enumerate(subsets):
            key=','.join(map(str,subset));trace=c['proj'][key]
            if not trace:raise AssertionError('NO_TRACE')
            if any(len(z)!=len(vv) for z in trace):raise AssertionError('INVALID_STATE_DIM')
            reached=trace[-1]
            if tuple(reached[j] for j in subset)!=tuple(c['bad'][j] for j in subset):
                raise AssertionError((filename,key,'PROJECTION_DOES_NOT_MATCH_BAD'))
            parts=[check(f'proj{ix}_init',func(p,trace[0]),'sat')]
            for j,(s0,s1) in enumerate(zip(trace,trace[1:])):
                parts.append(check(f'proj{ix}_step{j}',func(t,s0+s1),'sat'))
            witnesses[key]={'indices':subset,'observed_projection':[reached[j] for j in subset],
                            'original_reachable_states':trace,'checks':parts}
        # Exact bad state is either unsafe or leads to original source violation.
        bad_path=c['bad_path'];assert bad_path[0]==c['bad']
        unsafe_steps=[]
        for i,(x,y) in enumerate(zip(bad_path,bad_path[1:])):
            unsafe_steps.append(check(f'badpath_step{i}',func(t,x+y),'sat'))
        unsafe=check('bad_endpoint_not_post','(not '+func(q,bad_path[-1])+')','sat')
        sanity=check('bad_endpoint_post',func(q,bad_path[-1]),'unsat')
        inv_now='(INV '+' '.join(vv)+')';inv_next='(INV '+' '.join(v+'!' for v in vv)+')'
        full={
          'init':check('original_invariant_init','(and ('+p+' '+' '.join(vv)+') (not '+inv_now+'))','unsat',True),
          'consecution':check('original_invariant_step','(and '+inv_now+' ('+t+' '+' '.join(variables)+') (not '+inv_next+'))','unsat',True),
          'post':check('original_invariant_post','(and '+inv_now+' (not ('+q+' '+' '.join(vv)+')))','unsat',True),
        }
        # Unsafe fake state cannot be an actual Pre state, otherwise real program unsafe.
        not_real_init=check('unsafe_fake_not_pre',func(p,c['bad']),'unsat')
        log[filename]={
          'original_git_blob':h,'original_sha256':hashlib.sha256(data).hexdigest(),
          'source_state_variables':vv,'lower_bound':f'At least one relation involving >= {k+1} distinct source variables is required in every safety-inductive invariant that is a CONJUNCTION of predicates each of support <= k, with no auxiliary state.',
          'excluded_max_predicate_arity':k,'constructive_sufficient_invariant_arity':k+1,
          'excluded_k_ary_projection_witnesses':witnesses,
          'spurious_recombined_state':c['bad'],'source_verified_bad_path':bad_path,
          'source_verified_bad_steps':unsafe_steps,'source_post_negative':unsafe,
          'source_post_positive_unsat':sanity,'source_original_full_invariant_three_vc':full,
          'sufficient_invariant_HUMAN_PROPOSED':c['invariant'],
          'spurious_original_pre_unsat':not_real_init,
          'not_claimed':'This is not a universal lower bound for disjunctions of low-arity constraints, nor any machine-learned autonomous success.'
        }
        print(f'{filename}: source verified, projected {len(subsets)} × arity{k} real traces, '
              f'unsafe recombination, exact full 3VC. MIN_ARITY {k+1} in conjunctive predicate grammar',flush=True)
    r={'schema':'NEUMANN.Q3.AUTHENTIC_ORIGINAL_KWISE_CONJUNCTION_ARITY_BARRIER.v1',
       'status':'SCOPED_EXACT_MINIMAL_INTERACTION_ARITY_PROVED',
       'date':'2026-10-22','source_upstream':UPSTREAM,
       'original_count':len(log),'original_sha_verified':len(log),'proofs':log,
       'class_theorem':'Let R be original-source reachable states, and let I=AND_j P_j(s_Sj), |Sj|<=k, include R and be inductive. Any state t whose every k-variable projection equals a projection of some R element must be included in I; an original-source path from t to a Post violation contradicts I subset Post, hence no such I exists. Independently verified full-source invariant with max predicate support k+1 proves exact minimum within conjunction-of-local-predicates class.',
       'source_arity_lower_bound_distribution':{'3_vars_required':3,'4_vars_required':1},
       'verified_k_projection_witness_groups':sum(len(v['excluded_k_ary_projection_witnesses']) for v in log.values()),
       'both_SMT_backends':a.cvc5,'total_query_count_per_backend':queries,'query_result_counts':counts,
       'cost_wall_s':round(time.perf_counter()-t0,6),'neural_training_calls':0,'human_supplied_witnesses':True,
       'previously_opened_sources':True,'global_Q1_to_Q7':'OPEN','new_learning_only_capability':'NOT_ESTABLISHED'}
    out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print('SUMMARY',json.dumps({k:v for k,v in r.items() if k!='proofs'},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
