"""FGSR-Q3 opened-development symmetry-quotient ORIGINAL-SAFETY test.

Automatically read permutation closure generators from authentic Horn source.
Transport/semantics preconditions fail closed. No learned proposal; Q1-Q7 OPEN.
"""
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import time
import urllib.request

SRC="https://raw.githubusercontent.com/chc-comp/chc-comp26-benchmarks/b4fa7a708e5863bbcdb5de50d692ead3a67cbedc/ultimate/LIA-NonLin/33_double_lock_p1_vs_simplified_000.smt2"
SRC_SHA="2dfd3f531151113401aca614ad3e4176dae77ebcb326abbbcc456551a9a8f645"
OUT=Path(os.environ.get("FGSR_RESULT","symmetry_receipt.json"))
CAP=20

def top_level(s):
    depth=0;st=0;result=[];quoted=False;comment=False
    for i,c in enumerate(s):
        if c=="\n":comment=False
        if not quoted and c==";":comment=True
        if comment:continue
        if c=="|":quoted=not quoted
        if quoted:continue
        if c=="(":
            if depth==0:st=i
            depth+=1
        elif c==")":
            depth-=1
            if depth<0:raise ValueError("unbalanced_source")
            if depth==0:result.append(s[st:i+1])
    if depth:raise ValueError("unbalanced_source_final")
    return result

def close_pairs(s):
    all_=top_level(s)
    ds=[x for x in all_ if x.startswith("(declare-fun |Inv|")]
    if len(ds)!=1 or len(re.findall(r"\bInt\b",ds[0]))!=8:
        raise ValueError("unsupported_relation_sort")
    assertions=[x for x in all_ if x.startswith("(assert ")]
    expected=[]
    pat=re.compile(r"\(=>\s+\(and\s+\(Inv\s+([A-Za-z0-9_\s]+)\)\s+true\s*\)\s+\(Inv\s+([A-Za-z0-9_\s]+)\)\s*\)")
    for assertion in assertions:
        found=pat.search(assertion)
        if not found:continue
        left=found.group(1).split();right=found.group(2).split()
        if len(left)!=8 or len(right)!=8 or len(set(left))!=8 or sorted(left)!=sorted(right):continue
        movement=[i for i,(a,b) in enumerate(zip(left,right)) if a!=b]
        if len(movement)!=2:continue
        i,j=movement
        if left[i]==right[j] and left[j]==right[i]:
            expected.append((i,j))
    if sorted(expected)!=[(3,4),(5,6)]:
        # This source-specific bound is registered from inspected opened source.
        raise ValueError("unsupported_or_missing_independently_closed_symmetries:"+str(expected))
    return expected,assertions

def canonical_expr(args,pairs):
    a=args[:]
    for i,j in pairs:
        x,y=a[i],a[j]
        # Correct only for disjoint pairs and all-Int input.
        a[i]=f"(ite (<= {x} {y}) {x} {y})"
        a[j]=f"(ite (<= {x} {y}) {y} {x})"
    return "(Inv "+" ".join(a)+")"

def rewrite_original(s,pairs):
    atom=re.compile(r"\(Inv\s+((?:[A-Za-z0-9_\|]+\s+){7}[A-Za-z0-9_\|]+)\)")
    hits=[0]
    def sub(m):
        args=m.group(1).split()
        if len(args)!=8:raise ValueError("non_simple_atom")
        hits[0]+=1
        return canonical_expr(args,pairs)
    rewrite=atom.sub(sub,s)
    if hits[0]<80 or atom.search(rewrite):raise ValueError("incomplete_atom_rewrite "+str(hits))
    # Original 48 assertions preserved verbatim except Inv argument canonicalization.
    return rewrite,hits[0]

def check_canonical_invariance(pairs):
    rng=random.Random(20261016)
    for _ in range(2048):
        inp=[rng.randint(-9,13) for i in range(8)]
        def norm(a):
            b=a[:]
            for i,j in pairs:
                if b[i]>b[j]:b[i],b[j]=b[j],b[i]
            return b
        expected=norm(inp)
        for i,j in pairs:
            x=inp[:];x[i],x[j]=x[j],x[i]
            if norm(x)!=expected:raise ValueError("canonicalization_not_invariant")

def run_native(path):
    libpath=Path(__import__("z3").__file__).parent/"lib/libz3.so"
    if not libpath.exists():raise ValueError("missing pinned z3 library")
    lib=C.CDLL(str(libpath))
    lib.Z3_mk_config.restype=C.c_void_p
    lib.Z3_mk_context.argtypes=[C.c_void_p];lib.Z3_mk_context.restype=C.c_void_p
    lib.Z3_del_config.argtypes=[C.c_void_p]
    lib.Z3_del_context.argtypes=[C.c_void_p]
    lib.Z3_eval_smtlib2_string.argtypes=[C.c_void_p,C.c_char_p]
    lib.Z3_eval_smtlib2_string.restype=C.c_char_p
    cfg=lib.Z3_mk_config()
    ctx=lib.Z3_mk_context(cfg)
    lib.Z3_del_config(cfg)
    try:
        ans=lib.Z3_eval_smtlib2_string(ctx,path.read_bytes())
        val=(ans or b"").decode(errors="replace").strip()
    finally:
        lib.Z3_del_context(ctx)
    print(val)
    return val

def invoke(path):
    start=time.perf_counter_ns()
    try:
        p=subprocess.run([sys.executable,__file__,"--solver",str(path)],
                         capture_output=True,text=True,stdin=subprocess.DEVNULL,timeout=CAP,check=False)
        val=p.stdout.strip()
        if val in ("sat","unsat") and p.returncode==0:status="DECIDED_"+val.upper()
        elif val=="unknown" and p.returncode==0:status="UNKNOWN"
        else:status="ERROR"
        return {"status":status,"stdout":val[:200],"stderr":p.stderr[:320],
                "exit_code":p.returncode,"wall_ms":round((time.perf_counter_ns()-start)/1e6,3)}
    except subprocess.TimeoutExpired:
        return {"status":"TIMEOUT","wall_ms":round((time.perf_counter_ns()-start)/1e6,3)}

def main():
    start=time.perf_counter_ns()
    rec={"name":"FGSR-Q3 opened nonlearned permutation quotient speed probe",
         "source_sha256_expected":SRC_SHA,"neural_calls":0,
         "unmodified_original":True,"model_training":False,"global_Q":"OPEN",
         "case":"OPENED_48_CHC_CONCURRENCY","attempts_per_arm":1,
         "verdict":"INCOMPLETE"}
    try:
        original=urllib.request.urlopen(SRC,timeout=30).read()
        if hashlib.sha256(original).hexdigest()!=SRC_SHA:raise ValueError("SOURCE_SHA_MISMATCH")
        text=original.decode("utf8")
        pairs,rules=close_pairs(text)
        check_canonical_invariance(pairs)
        transformed,atoms=rewrite_original(text,pairs)
        if len(rules)!=48 or len(top_level(transformed))!=len(top_level(text)):
            raise ValueError("original_rule_count_or_form_changed")
        rec["source_assertions"]=len(rules)
        rec["detected_swap_generators"]=pairs
        rec["canonicalized_inv_atoms"]=atoms
        rec["equivalence_argument"]=(
          "Old models must be closed under each universally quantified unguarded swap "
          "rule. Restrict old models to canonical tuples for old->new. Define old R(x) "
          "=new R(canon(x)) for new->old; rewritten clause bodies/heads then coincide. "
          "All original Horn clauses retained and all rules rewritten uniformly."
        )
        rec["permutation_replay_tests"]=2048*len(pairs)
        rec["transformed_sha256"]=hashlib.sha256(transformed.encode()).hexdigest()
        original_path=Path("/tmp/fgsr_original_48.smt2")
        transformed_path=Path("/tmp/fgsr_symmetry_quotient_48.smt2")
        original_path.write_bytes(original)
        transformed_path.write_text(transformed)
        import z3
        rec["z3_version"]=z3.get_version_string()
        rec["paired_original"]=invoke(original_path)
        rec["paired_quotient"]=invoke(transformed_path)
        old=rec["paired_original"]["status"]
        new=rec["paired_quotient"]["status"]
        rec["verdict"]="QUOTIENT_DECIDED" if new.startswith("DECIDED_") else (
            "NO_RESCUE" if new in ("TIMEOUT","UNKNOWN") else "QUOTIENT_ERROR")
        if old.startswith("DECIDED_") and new.startswith("DECIDED_") and old!=new:
            rec["verdict"]="REJECT_CONTRADICTORY_VERDICT"
    except Exception as exc:
        rec["verdict"]="BLOCKED_PRECONDITION"
        rec["exception"]=type(exc).__name__+": "+str(exc)[:900]
    rec["total_wall_ms"]=round((time.perf_counter_ns()-start)/1e6,3)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(rec,indent=2)+"\n")
    print("FGSR_QUOTIENT",rec["verdict"])
    print("ORIGINAL",rec.get("paired_original"))
    print("QUOTIENT",rec.get("paired_quotient"))
    print("Q1_Q7",rec["global_Q"])

if __name__=="__main__":
    if len(sys.argv)>2 and sys.argv[1]=="--solver":
        run_native(Path(sys.argv[2]))
    else:main()
