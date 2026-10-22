#!/usr/bin/env python3
"""Retrospective independent source-only Z3 SPACER native baseline on exact preregistered 12.
No invariant proposals, no learned training. SPACER UNSAT is a source decision,
not a Z3+cvc5 inductive invariant triple. Preserves UNKNOWN and unsafe SAT.
"""
from __future__ import annotations
import argparse,ctypes,hashlib,json,pathlib,re,time

def balanced(src:str,pos:int)->str:
    d=0
    for j in range(pos,len(src)):
        d+=(src[j]=='(')-(src[j]==')')
        if not d:return src[pos:j+1]
    raise ValueError('BAD_PARENS')

def make_source_query(source:str,timeout_ms:int):
    marker=re.search(r'\(synth-inv\s+\S+\s+',source)
    if marker is None: raise ValueError('NO_SYNTH_INV')
    sig=balanced(source,marker.end())
    names=re.findall(r'\(\s*([^\s()]+)\s+Int\s*\)',sig)
    defs=[balanced(source,m.start()) for m in re.finditer(r'\(define-fun\s+',source)]
    if not names or len(defs)!=3 or len(set(names))!=len(names):raise ValueError('BAD_SOURCE_SCHEMA')
    fns=[re.search(r'\(define-fun\s+([^\s()]+)',x).group(1) for x in defs]
    now=' '.join(names); future=' '.join([x+'!' for x in names]);both=' '.join(names+[x+'!' for x in names])
    prog=['(set-logic HORN)',f'(set-option :timeout {timeout_ms})']
    prog += [f'(declare-var {x} Int)\n(declare-var {x}! Int)' for x in names]
    prog += defs
    prog += ['(declare-rel Reach ('+' '.join(['Int']*len(names))+'))','(declare-rel Unsafe ())',
             f'(rule (=> ({fns[0]} {now}) (Reach {now})))',
             f'(rule (=> (and (Reach {now}) ({fns[1]} {both})) (Reach {future})))',
             f'(rule (=> (and (Reach {now}) (not ({fns[2]} {now}))) Unsafe))',
             '(query Unsafe)']
    return '\n'.join(prog)+'\n'

class Z3:
    def __init__(self):
        # Pin the backend to the z3-solver wheel if present; the Ubuntu
        # apt libz3 can be an older version with incompatible fixedpoint parser.
        try:
            import z3 as pyz3
            wheel=pathlib.Path(pyz3.__file__).parent/'lib'/'libz3.so'
            if not wheel.exists():wheel=pathlib.Path(pyz3.__file__).parent/'lib'/'libz3.so.4'
            if not wheel.exists():raise RuntimeError('PINNED_WHEEL_LIBZ3_NOT_FOUND')
            z=ctypes.CDLL(str(wheel))
        except ImportError:
            z=ctypes.CDLL('libz3.so.4')
        self.z=z
        z.Z3_mk_config.restype=ctypes.c_void_p
        z.Z3_mk_context.argtypes=[ctypes.c_void_p];z.Z3_mk_context.restype=ctypes.c_void_p
        z.Z3_eval_smtlib2_string.argtypes=[ctypes.c_void_p,ctypes.c_char_p];z.Z3_eval_smtlib2_string.restype=ctypes.c_char_p
        z.Z3_del_context.argtypes=[ctypes.c_void_p];z.Z3_del_config.argtypes=[ctypes.c_void_p]
    def query(self,script:str):
        z=self.z;c=z.Z3_mk_config();p=z.Z3_mk_context(c)
        try:
            v=z.Z3_eval_smtlib2_string(p,script.encode())
            if not v: return 'ERROR_NULL'
            outs=v.decode().strip().splitlines()
            tokens=[x for x in outs if x in ('sat','unsat','unknown')]
            return tokens[-1] if tokens else 'ERROR_'+repr(outs[:2])[:80]
        finally: z.Z3_del_context(p);z.Z3_del_config(c)

def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=pathlib.Path,required=True);p.add_argument('--input',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--timeout-ms',type=int,default=5000)
    a=p.parse_args();assert a.timeout_ms==5000
    d=json.loads(a.manifest.read_text());r=[];z=Z3();t=time.perf_counter()
    for item in d['cases']:
        b=(a.input/item['name']).read_bytes()
        sha=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
        x={'original_name':item['name'],'source_git_blob_sha1':sha,'source_exact':sha==item['sha'] and len(b)==item['size']}
        start=time.perf_counter()
        if not x['source_exact']: x.update(status='ABSTAIN_SOURCE_MISMATCH')
        else:
            try:
                script=make_source_query(b.decode(),a.timeout_ms)
                x.update(query_sha256=hashlib.sha256(script.encode()).hexdigest(),status=z.query(script))
            except Exception as ex:x.update(status='ABSTAIN',error=str(ex)[:180])
        x['time_ms']=round(1000*(time.perf_counter()-start),3)
        r.append(x);print(item['name'],x['status'],x['time_ms'],flush=True)
    report={'type':'SOURCE_ONLY_SPACER_POSTHOC_STRONG_CLASSICAL_COMPARATOR','scope':'retrospective after full 12 case first experiment; not preregistered timing competition','actual_unmodified_sources':len(r),'unsat_count':sum(x['status']=='unsat' for x in r),'sat_count':sum(x['status']=='sat' for x in r),'unknown_or_error_count':sum(x['status'] not in ('sat','unsat') for x in r),'wall_s':round(time.perf_counter()-t,3),'rows':r,'global_Q1_Q7':'OPEN'}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('STRONG_SPACER_SUMMARY',report['unsat_count'],'/',len(r),'original safe',flush=True)
if __name__=='__main__':main()