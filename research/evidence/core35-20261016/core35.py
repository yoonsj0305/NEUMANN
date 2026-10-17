"""NEUMANN CORE-35: real RustHorn CHC evidence, development-only.

No learned model is used. Human-proposed witness is POST-HOC.
Repro: python core35.py --source-dir /path/to/smt2
        python core35.py --fetch-upstream
Requires native libz3.so (a Python z3-solver package is not required).
"""
from __future__ import annotations
import argparse, ctypes as C, hashlib, json, pathlib, subprocess, sys, time
from ctypes.util import find_library
from urllib.request import urlopen

ROOT=pathlib.Path(__file__).resolve().parent
REV='e5a86a1ad252fe1df75e06814769ec1d14540032'
CASES={
'safe': ('trees-2-inc-all-safe.smt2','75f06780eaa4d48f48c56228e007a9dbe87a9df6','713e61bb9abe535491e93a36581d1d16f2ba617e454366a1b589d692b0453456'),
'unsafe': ('trees-2-inc-all-unsafe.smt2','e3029c62337109beace3c9c318ac4c316a848c20','df1b8a1d09829f72ba886ad5ae1f0460ae315a946fd55acdd70e6620419eb8bb')}

# After examining the full real source, a human wrote this certificate.
# It is NOT inferred by a frozen neural model, nor target-holdout-clean.
WITNESS=r'''
(define-fun-rec SUM ((t %Tree)) Int
 (ite (= t %Tree-1) 0 (+ (SUM (%Tree-0.0 t)) (%Tree-0.1 t) (SUM (%Tree-0.2 t)))))
(define-fun-rec SIZE ((t %Tree)) Int
 (ite (= t %Tree-1) 0 (+ 1 (SIZE (%Tree-0.0 t)) (SIZE (%Tree-0.2 t)))))
(define-fun %sum ((t %Tree) (n Int)) Bool (= n (SUM t)))
(define-fun %sum.0 ((t %Tree) (n Int)) Bool (= n (SUM t)))
(define-fun %size ((t %Tree) (n Int)) Bool (= n (SIZE t)))
(define-fun %size.0 ((t %Tree) (n Int)) Bool (= n (SIZE t)))
(define-fun %inc ((p ~Mut<%Tree>)) Bool
 (= (SUM (~ret<%Tree> p)) (+ (SUM (~cur<%Tree> p)) (SIZE (~cur<%Tree> p)))))
(define-fun %inc.0 ((p ~Mut<%Tree>)) Bool
 (= (SUM (~ret<%Tree> p)) (+ (SUM (~cur<%Tree> p)) (SIZE (~cur<%Tree> p)))))
(define-fun %main.5 ((t %Tree) (initialSum Int) (n Int) (newSum Int) (bad Bool) (ret Bool)) Bool
 (= bad ret))
(define-fun %main ((ret Bool)) Bool (not ret))
'''

def hashes(data):
    return (hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),hashlib.sha256(data).hexdigest())

def get_source(key,root,fetch):
    name,blob,sha=CASES[key]
    if fetch:
        url=f'https://raw.githubusercontent.com/chc-comp/rust-horn/{REV}/{name}'
        with urlopen(url,timeout=20) as fh:data=fh.read()
        root.mkdir(parents=True,exist_ok=True)
        (root/name).write_bytes(data)
    else:
        data=(root/name).read_bytes()
    actual=hashes(data)
    if actual!=(blob,sha):raise ValueError(f'{key} SOURCE HASH MISMATCH: {actual}')
    return data.decode('utf8')

def top_level(s):
    expressions=[];depth=0;start=None;comment=False
    for i,ch in enumerate(s):
        if ch=='\n':comment=False
        if comment:continue
        if ch==';':comment=True;continue
        if ch=='(':
            if depth==0:start=i
            depth+=1
        elif ch==')':
            depth-=1
            if depth<0:raise ValueError('unbalanced parentheses')
            if depth==0:expressions.append(s[start:i+1])
    if depth:raise ValueError('unbalanced end')
    return expressions

def clauses(s,witness=WITNESS):
    exprs=top_level(s)
    datatypes=[e for e in exprs if e.startswith('(declare-datatypes')]
    rules=[e for e in exprs if e.startswith('(assert ')]
    if len(datatypes)!=3 or len(rules)!=13:raise ValueError('unexpected AST; fail closed')
    if len([e for e in exprs if e.startswith('(check-sat')])!=1:raise ValueError('missing original check-sat')
    prefix='(set-logic ALL)\n'+'\n'.join(datatypes)+'\n'+witness+'\n'
    for rule in rules:
        assert rule.endswith(')')
        yield prefix+'(assert (not '+rule[len('(assert '):-1]+'))\n(check-sat)\n'

def native_evaluate(source):
    lib=C.CDLL(find_library('z3'))
    lib.Z3_mk_config.restype=C.c_void_p
    lib.Z3_mk_context.argtypes=[C.c_void_p];lib.Z3_mk_context.restype=C.c_void_p
    lib.Z3_del_config.argtypes=[C.c_void_p];lib.Z3_del_context.argtypes=[C.c_void_p]
    lib.Z3_eval_smtlib2_string.argtypes=[C.c_void_p,C.c_char_p];lib.Z3_eval_smtlib2_string.restype=C.c_char_p
    lib.Z3_get_error_code.argtypes=[C.c_void_p];lib.Z3_get_error_code.restype=C.c_int
    handler_type=C.CFUNCTYPE(None,C.c_void_p,C.c_int)
    handler=handler_type(lambda ctx,error:None)
    lib.Z3_set_error_handler.argtypes=[C.c_void_p,handler_type]
    cfg=lib.Z3_mk_config();ctx=lib.Z3_mk_context(cfg);lib.Z3_del_config(cfg)
    lib.Z3_set_error_handler(ctx,handler)
    try:
        raw=lib.Z3_eval_smtlib2_string(ctx,source.encode('utf8'))
        answer=(raw or b'').decode('utf8','replace').strip()
        err=lib.Z3_get_error_code(ctx)
    finally:lib.Z3_del_context(ctx)
    return answer if err==0 and answer in ('sat','unsat','unknown') else 'ERROR'

def child(cmd,source):
    # Fresh process + fresh C context = avoid solver-state contamination.
    if cmd=='eval':print(json.dumps({'verdict':native_evaluate(source)}))

def one(source,timeout):
    start=time.perf_counter_ns()
    try:
        cp=subprocess.run([sys.executable,__file__,'--child','eval'],input=source,text=True,
                          capture_output=True,timeout=timeout)
        verdict=json.loads(cp.stdout)['verdict'] if cp.returncode==0 else 'ERROR'
    except (subprocess.TimeoutExpired,ValueError,KeyError,json.JSONDecodeError):
        verdict='TIMEOUT_OR_ERROR'
    return {'verdict':verdict,'wall_ms':round((time.perf_counter_ns()-start)/1e6,3)}

def audit(root,fetch=False,baseline_timeout=10,rule_timeout=4):
    data={k:get_source(k,root,fetch) for k in ('safe','unsafe')}
    result={'status':'INCOMPLETE', 'experiment':'CORE-35','global_Q1_Q7':'OPEN',
      'learned_model_calls':0,'human_proposed_witness':True,'external_repo':'chc-comp/rust-horn',
      'external_revision':REV,'source_hash_verified':True,'baseline_timeout_s':baseline_timeout,
      'per_clause_timeout_s':rule_timeout,'cases':{}}
    for k,src in data.items():
        raw=one(src,baseline_timeout)
        checks=[one(c,rule_timeout) for c in clauses(src)]
        result['cases'][k]={'source_sha256':CASES[k][2],'source_git_blob':CASES[k][1],
           'direct_original':raw,'rules':[x['verdict'] for x in checks],
           'clause_wall_ms':[x['wall_ms'] for x in checks],
           'all_original_clauses_certified':all(x['verdict']=='unsat' for x in checks)}
    safe=result['cases']['safe'];unsafe=result['cases']['unsafe']
    # Negative: corrupt human witness. A broken invariant must not certify the safe original.
    poisoned=WITNESS.replace('(+ (SUM (~cur<%Tree> p)) (SIZE (~cur<%Tree> p)))', '(SUM (~cur<%Tree> p))')
    assert poisoned!=WITNESS
    poison_checks=[one(list(clauses(data['safe'],poisoned))[1],rule_timeout)]
    result['negative_controls']={'poisoned_safe_rejected':any(x['verdict']=='sat' for x in poison_checks),
      'poisoned_rules':[x['verdict'] for x in poison_checks],
      'unsafe_original_rejected_by_witness':any(x=='sat' for x in unsafe['rules'])}
    result['status']=('EXTERNAL_SAFE_WITNESS_CERTIFIED_LEARNED_OPEN'
      if safe['all_original_clauses_certified'] and not unsafe['all_original_clauses_certified']
         and result['negative_controls']['poisoned_safe_rejected'] and
         result['negative_controls']['unsafe_original_rejected_by_witness']
      else 'ABSTAIN_VERIFICATION_FAILURE')
    result['scientific_limit']='Witness invented by researcher after seeing source; no learned discovery, no Q closure; direct vs certificate do not charge human work equally.'
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-dir',type=pathlib.Path,default=ROOT)
    parser.add_argument('--fetch-upstream',action='store_true')
    parser.add_argument('--output',type=pathlib.Path,default=ROOT/'receipt_core35.json')
    parser.add_argument('--child',default='')
    args=parser.parse_args()
    if args.child:child(args.child,sys.stdin.read());return
    obj=audit(args.source_dir,args.fetch_upstream)
    args.output.write_text(json.dumps(obj,indent=2)+'\n')
    print(json.dumps(obj,indent=2))

if __name__=='__main__':main()
