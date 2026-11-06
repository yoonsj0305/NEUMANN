"""G2 alternate post-first SOURCE-proof for two negative numeral parser errors.

No original SyGuS synthesizer is called. No original FIRST rewritten.
Both original published Git blobs and candidate bytes are hash-pinned.
Source LIA old negative integer -N is normalized to modern SMT-LIB
(- N) only for the independent UNSAT checker. This is NOT learned Q3.
"""
from __future__ import annotations

import hashlib,json,re,subprocess,sys,tempfile
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[2]
ERR=ROOT/"docs/experiments/G2_POSTFIRST_NEGATIVE_INT_SMT_REPLAY_CONTRACT_2026_11_06.json"

def sha(data:bytes):
    return hashlib.sha256(data).hexdigest()

def blob(data:bytes):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def forms(src:str):
    """Independent source expression reader, ignoring S-expr comments."""
    out=[];i=0;depth=0;st=None;comment=False
    while i<len(src):
        c=src[i]
        if comment:
            if c=="\n":comment=False
            i+=1;continue
        if c==';':comment=True
        elif c=='(':
            if depth==0:st=i
            depth+=1
        elif c==')':
            depth-=1
            if depth<0:raise ValueError("BAD_SMT_SOURCE")
            if depth==0:
                out.append(src[st:i+1])
                st=None
        i+=1
    if depth:raise ValueError("UNBALANCED_SMT_SOURCE")
    return out

def modern_int_literals(expr:str)->tuple[str,int]:
    """Exact legacy LIA negative INTEGER lexical normalization; no strings."""
    if '"' in expr or ';' in expr:
        raise ValueError("UNSUPPORTED_STRING_OR_COMMENT_IN_INTEGER_PROOF")
    # Boundaries: not a subtraction operator and not identifiers with hyphens.
    pattern=r"(?<![A-Za-z0-9_!.\-])-(\d+)(?=[\s\)])"
    result,n=re.subn(pattern,lambda m:"(- "+m.group(1)+")",expr)
    return result,n

def ground(source:str,candidate:str,mutant=False)->tuple[list[tuple[str,str]],int]:
    raw=forms(source)
    defs=[x for x in raw if re.match(r"^\(\s*define-fun\s+",x)]
    aliases={}
    for f in defs:
        m=re.match(r"^\(\s*define-fun\s+(\S+)\s+",f)
        aliases[m.group(1)]=f
    inv_spec=next(x for x in raw if re.match(r"^\(\s*synth-inv\s+",x))
    m=re.match(r"^\(\s*synth-inv\s+(\S+)\s+",inv_spec)
    name=m.group(1)
    typed=re.findall(r"\(\s*(\w+)\s+Int\s*\)",inv_spec)
    if not typed or len(typed)>5:
        raise ValueError("BAD_INT_SIGNATURE")
    inv_constraint=next(x for x in raw if re.match(r"^\(\s*inv-constraint\s+",x))
    spec=re.fullmatch(r"\(\s*inv-constraint\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*\)",inv_constraint)
    if not spec or spec.group(1)!=name:
        raise ValueError("NO_NATIVE_INV_SEMANTICS")
    _,pre,trans,post=spec.groups()
    if not all(k in aliases for k in (pre,trans,post)):
        raise ValueError("MISSING_ORIGINAL_DEFINITIONS")
    converted=[];changes=0
    for d in defs:
        fixed,n=modern_int_literals(d)
        changes+=n
        converted.append(fixed)
    # Require actual old tokens, otherwise this exact diagnostic
    # audit is not applicable (prevents arbitrary rewrite).
    if changes<1:raise ValueError("NO_LEGACY_NEGATIVE_INTEGER_TO_FIX")
    var=typed
    def call(f,v):return "("+f+" "+" ".join(v)+")"
    nxt=[x+"!" for x in var]
    declarations="\n".join("(declare-const "+x+" Int)" for x in var+nxt)
    candidate_text=("(define-fun "+name+" (("+" Int) (".join(var)+" Int)) Bool false)"
      if mutant else candidate)
    base="(set-logic ALL)\n"+"\n".join(converted)+"\n"+candidate_text+"\n"+declarations+"\n"
    obligations=[
       ("init","(and "+call(pre,var)+" (not "+call(name,var)+"))"),
       ("step","(and "+call(name,var)+" "+call(trans,var+nxt)+" (not "+call(name,nxt)+"))"),
       ("safe","(and "+call(name,var)+" (not "+call(post,var)+"))")
    ]
    return [(label,base+"(assert "+assertion+")\n(check-sat)\n") for label,assertion in obligations],changes

def smt_unsat(script:str):
    with tempfile.NamedTemporaryFile("w",encoding="utf8",suffix=".smt2") as f:
        f.write(script);f.flush()
        p=subprocess.run(["cvc5","--lang=smt2",f.name],text=True,capture_output=True,timeout=8)
    answer=[t.strip() for t in p.stdout.splitlines() if t.strip()]
    return {"unsat":p.returncode==0 and answer==["unsat"],"exit":p.returncode,
            "answer":answer[:3],"stderr_tail":p.stderr[-190:]}

def audit(first_path:Path):
    contract=json.loads(ERR.read_text())
    raw=first_path.read_bytes()
    if sha(raw)!=contract["original_inv_FIRST_sha256"]:
        raise ValueError("ORIGINAL_FIRST_IMMUTABLE_SHA_CHANGED")
    first=json.loads(raw)
    if first["cohort"]!="INV_INDUCTION" or len(first["rows"])!=12:
        raise ValueError("ORIGINAL_DENOMINATOR_CHANGED")
    results=[]
    for t in contract["target_cases"]:
        row=next(r for r in first["rows"] if r["file"]==t["file"])
        if row["status"]!="NATIVE_CANDIDATE_NOT_PROVEN":
            raise ValueError("ORIGINAL_FIRST_REASON_CHANGED")
        candidate=row["candidate"]
        if sha(candidate.encode())!=t["candidate_sha256"]:
            raise ValueError("PINNED_NATIVE_PROGRAM_CHANGED")
        url="https://raw.githubusercontent.com/SyGuS-Org/benchmarks/13c8deb68a873635879c9a69bc78caebd340f646/comp/2018/Inv_Track/"+t["file"]
        with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G2-independent-legacy-integer"}),timeout=40) as x:
            source=x.read()
        if blob(source)!=t["source_git_blob"] or blob(source)!=row["blob"]:
            raise ValueError("EXTERNAL_ORIGINAL_SOURCE_GIT_BLOB_CHANGED")
        assertions,n=ground(source.decode(),candidate)
        proofs=[{"phase":label,**smt_unsat(smt)} for label,smt in assertions]
        assert len(proofs)==3
        mutant_assertions,_=ground(source.decode(),candidate,mutant=True)
        mutant=smt_unsat(mutant_assertions[0][1])
        passed=all(p["unsat"] for p in proofs)
        if mutant["unsat"]:
            raise ValueError("FALSE_INVARIANT_MUTANT_NOT_REJECTED")
        results.append({"name":t["file"],"first_program_sha":sha(candidate.encode()),
            "original_source_blob":blob(source),"legacy_integer_tokens_corrected":n,
            "all_three_universal_INVARIANT_obligations_valid":passed,
            "independent_obligations":proofs,
            "deliberately_false_invariant_mutant_refuted":not mutant["unsat"]})
    return {"schema":"neumann.q3.g2.legacy-negative-independent-original-reproof.v1",
       "audit_pass":len(results)==2 and all(r["all_three_universal_INVARIANT_obligations_valid"] for r in results),
       "first_INV_SHA256":sha(raw),
       "original_cases_reproved":len(results),
       "original_native_synthesis_rerun":False,
       "neumann_student_training":False,
       "previous_independent_verified_first":7,
       "new_source_only_reproof_valid":sum(r["all_three_universal_INVARIANT_obligations_valid"] for r in results),
       "total_exact_original_INV_verified_including_reproof":7+sum(r["all_three_universal_INVARIANT_obligations_valid"] for r in results),
       "remaining_original_12s_timeout":2,"remaining_native_no_program":1,
       "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
       "cases":results}

if __name__=="__main__":
    try:
        r=audit(Path(sys.argv[1]))
        print(json.dumps(r,indent=2,sort_keys=True))
        if not r["audit_pass"]:raise SystemExit(1)
    except Exception as e:
        print("G2_INDEPENDENT_INTEGER_PROOF_FAIL",repr(e),file=sys.stderr)
        raise SystemExit(2)
