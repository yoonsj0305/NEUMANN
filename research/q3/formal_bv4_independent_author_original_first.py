"""Q3 independent formal-spec transfer gate, 4-bit bitvector inverses.

This solver is deliberately bounded. The VM and grammar are human-coded.
Source cohort: 16 original signed>= inverse specs. Target cohort: 32
untouched signed<= or unsigned>= inverse specs, all 4-bit.
Run with --source BEFORE any --target. Never read a target spec while
building or freezing the learned policy. No reference solution is fetched.

Unlike earlier Q3 synthetic verification: no secret teacher/oracle is given
to candidate generation. The *published formal specification*, however, is
an authorized checker: all 16*16 input pairs are exhaustively evaluated.
"""
from __future__ import annotations
import collections, hashlib, itertools, json, pathlib, re, sys, time, urllib.request

ROOT="https://raw.githubusercontent.com/SyGuS-Org/benchmarks/13c8deb68a873635879c9a69bc78caebd340f646/comp/2019/General_Track/bv-conditional-inverses/"
OPS=["bvadd","bvand","bvashr0","bvashr1","bvlshr0","bvlshr1","bvmul","bvneg","bvnot","bvor","bvshl0","bvshl1","bvudiv0","bvudiv1","bvurem0","bvurem1"]
SOURCE=[f"find_inv_bvsge_{x}_4bit.sl" for x in OPS]
TARGET=[f"find_inv_{c}_{x}_4bit.sl" for c in ("bvsle","bvuge") for x in OPS]
assert len(SOURCE)==16 and len(TARGET)==32
assert set(SOURCE).isdisjoint(TARGET)
N=4;MASK=15
PAIRS=list(itertools.product(range(16),repeat=2))
MAX_CANDIDATES=5000

def canon(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"))
def sha(x):return hashlib.sha256(canon(x).encode()).hexdigest()

def parse_smt(raw):
    raw=re.sub(r";[^\n]*","",raw)
    toks=re.findall(r"\(|\)|[^\s()]+",raw)
    stack=[];root=[]
    for tok in toks:
        if tok=="(":
            new=[]
            if stack:stack[-1].append(new)
            else:root.append(new)
            stack.append(new)
        elif tok==")":
            if not stack:raise ValueError("ORPHAN_CLOSE")
            stack.pop()
        else:
            if not stack:raise ValueError("ATOM_OUTSIDE_FORM")
            stack[-1].append(tok)
    if stack:raise ValueError("UNCLOSED_SOURCE")
    return root

def parse_benchmark(raw):
    forms=parse_smt(raw);defs={}
    for form in forms:
        if form and form[0]=="define-fun":
            if len(form)!=5:raise ValueError("BAD_DEFINITION")
            defs[form[1]]=(form[2],form[4])
    synth=[f for f in forms if f and f[0]=="synth-fun"]
    constraint=[f[1] for f in forms if f and f[0]=="constraint"]
    if len(synth)!=1 or len(constraint)!=1:raise ValueError("EXPECTED_ONE_SYNTH_ONE_CONSTRAINT")
    f=synth[0]
    if f[1]!="inv" or len(f[2])!=2 or len(f)<5:raise ValueError("UNSUPPORTED_SYNTH_FUNCTION")
    if f[2][0][0]!="s" or f[2][1][0]!="t":raise ValueError("DIFFERENT_ARGUMENT_ORDER")
    grammar_tokens=set()
    def collect(node):
        if isinstance(node,list):
            for c in node:collect(c)
        else:grammar_tokens.add(node)
    collect(f[4])
    allowed={"bvneg","bvnot","bvadd","bvsub","bvand","bvlshr","bvor","bvshl"}
    allowed &= grammar_tokens
    return {"definitions":defs,"constraint":constraint[0],
            "allowed_operators":sorted(allowed),"source_len":len(raw)}

def signed(x):return x-16 if x&8 else x

def bv(op,a,b=None):
    if op=="bvneg":return (-a)&MASK
    if op=="bvnot":return (~a)&MASK
    if op=="bvadd":return (a+b)&MASK
    if op=="bvsub":return (a-b)&MASK
    if op=="bvmul":return (a*b)&MASK
    if op=="bvand":return a&b
    if op=="bvor":return a|b
    if op=="bvxor":return a^b
    if op=="bvshl":return (a<<b)&MASK
    if op=="bvlshr":return a>>b
    if op=="bvashr":return (signed(a)>>b)&MASK
    if op=="bvudiv":return MASK if b==0 else a//b
    if op=="bvurem":return a if b==0 else a%b
    raise ValueError("UNKNOWN_BV_OPERATOR "+op)

def expr(ast,env,defs,inv_value,depth=0):
    if depth>40:raise ValueError("FORMULA_RECURSION")
    if isinstance(ast,str):
        if ast in env:return env[ast]
        if ast=="true":return True
        if ast=="false":return False
        if ast.startswith("#x"):return int(ast[2:],16)
        if ast.startswith("#b"):return int(ast[2:],2)
        raise ValueError("UNKNOWN_ATOM "+ast)
    if not ast:raise ValueError("EMPTY_EXPR")
    op=ast[0];children=ast[1:]
    if op=="inv":return inv_value
    if op in defs:
        params,body=defs[op]
        vals=[expr(v,env,defs,inv_value,depth+1) for v in children]
        if len(vals)!=len(params):raise ValueError("BAD_DEFINITION_ARITY")
        frame=env.copy()
        for p,v in zip(params,vals):frame[p[0]]=v
        return expr(body,frame,defs,inv_value,depth+1)
    if op=="ite":
        test=expr(children[0],env,defs,inv_value,depth+1)
        return expr(children[1 if test else 2],env,defs,inv_value,depth+1)
    if op=="and":
        return all(expr(v,env,defs,inv_value,depth+1) for v in children)
    if op=="or":
        return any(expr(v,env,defs,inv_value,depth+1) for v in children)
    if op=="not":return not expr(children[0],env,defs,inv_value,depth+1)
    if op=="=>":return (not expr(children[0],env,defs,inv_value,depth+1) or
                        expr(children[1],env,defs,inv_value,depth+1))
    vals=[expr(v,env,defs,inv_value,depth+1) for v in children]
    if op=="=":return all(v==vals[0] for v in vals[1:])
    if op=="distinct":return len(set(vals))==len(vals)
    if op=="bvsge":return signed(vals[0])>=signed(vals[1])
    if op=="bvsgt":return signed(vals[0])>signed(vals[1])
    if op=="bvsle":return signed(vals[0])<=signed(vals[1])
    if op=="bvslt":return signed(vals[0])<signed(vals[1])
    if op=="bvuge":return vals[0]>=vals[1]
    if op=="bvugt":return vals[0]>vals[1]
    if op=="bvule":return vals[0]<=vals[1]
    if op=="bvult":return vals[0]<vals[1]
    if op in ("bvneg","bvnot"):return bv(op,vals[0])
    if op in ("bvadd","bvsub","bvmul","bvand","bvor","bvxor",
              "bvshl","bvlshr","bvashr","bvudiv","bvurem"):
        return bv(op,vals[0],vals[1])
    raise ValueError("UNSUPPORTED_FORMULA_OPERATOR "+op)

def allowed_table(problem):
    # Authorized mathematical specification, 256 input assignments, and
    # 16 possible inverse outputs. This is *complete verification*, not
    # private hidden target labels.
    d=problem["definitions"];formula=problem["constraint"]
    table=[]
    for s,t in PAIRS:
        env={"s":s,"t":t}
        mask=0
        for value in range(16):
            if expr(formula,env,d,value):
                mask |= (1<<value)
        if mask==0:raise ValueError("UNSAT_FOR_SOME_INPUT_PAIR")
        table.append(mask)
    return table

def bitvector_signature(ast, sig):
    op=ast[0]
    if op=="s":return tuple(x[0] for x in PAIRS)
    if op=="t":return tuple(x[1] for x in PAIRS)
    if op=="lit":return (ast[1],)*256
    if op in ("bvneg","bvnot"):
        return tuple(bv(op,a) for a in sig[ast[1]])
    return tuple(bv(op,a,b) for a,b in zip(sig[ast[1]],sig[ast[2]]))

def library():
    # Same universal finite grammar for cold and learned.
    accepted=[];signatures={};seen={}
    def add(ast):
        if ast in signatures:return
        vector=bitvector_signature(ast,signatures)
        if vector in seen:return
        signatures[ast]=vector;seen[vector]=ast;accepted.append(ast)
    bases=[("s",),("t",),("lit",0),("lit",7),("lit",8)]
    for a in bases:add(a)
    first=accepted[:]
    for op in ("bvnot","bvneg"):
        for a in first:add((op,a))
    for op in ("bvadd","bvsub","bvand","bvor","bvlshr","bvshl"):
        for a in first:
            for b in first:add((op,a,b))
    depth_one=accepted[:]
    for op in ("bvnot","bvneg"):
        for a in depth_one:
            if len(accepted)>=MAX_CANDIDATES:break
            add((op,a))
    for op in ("bvadd","bvsub","bvand","bvor","bvlshr","bvshl"):
        for a in depth_one:
            for b in first:
                if len(accepted)>=MAX_CANDIDATES:break
                add((op,a,b))
                add((op,b,a))
            if len(accepted)>=MAX_CANDIDATES:break
        if len(accepted)>=MAX_CANDIDATES:break
    return accepted,signatures

def instruction_count(p):
    return 1+sum(instruction_count(c) for c in p[1:] if isinstance(c,tuple))
def keywords(p):
    # Structural concepts: automatically extracted from source-certified
    # ASTs; there is no manual mapping from benchmark operation to solution.
    op=p[0]
    if op in ("s","t","lit"):return [("leaf",op)]
    op_children=tuple(c[0] for c in p[1:] if isinstance(c,tuple))
    out=[("root",op),("shape",op,op_children)]
    for c in p[1:]:
        if isinstance(c,tuple):out+=keywords(c)
    return out

def rank_baseline(p):
    return (instruction_count(p),canon(p))
def learn_order(solved,all_asts):
    freq=collections.Counter()
    for p in solved:
        for term in set(keywords(p)):freq[term]+=1
    if not freq:raise ValueError("SOURCE_NO_VERIFIED_PROGRAMS")
    # Structural probabilistic prior: identical full grammar;
    # learned ranking cannot invent unprovided primitives.
    def score(p):
        return sum(freq[k] for k in set(keywords(p)))
    return sorted(all_asts,key=lambda p:(-score(p),rank_baseline(p))),dict(
        sorted(((str(k),v) for k,v in freq.items()),key=lambda item:item[0]))

def solve(original,asts,sigs,check_budget=None):
    checks=0
    for ast in asts:
        if check_budget is not None and checks>=check_budget:break
        checks+=1
        if all(mask&(1<<v) for mask,v in zip(original,sigs[ast])):
            return ast,checks
    return None,checks

def fetch(name):
    with urllib.request.urlopen(ROOT+name,timeout=25) as h:
        raw=h.read(150001)
    if len(raw)>150000:raise ValueError("OVERSIZED_ORIGINAL")
    return raw.decode("utf-8")

def test_filename(name):
    if name not in SOURCE and name not in TARGET:
        raise ValueError("OUT_OF_PREDECLARED_SCOPE")

def source_only():
    import time
    started=time.perf_counter()
    asts,sigs=library()
    # Code/grammar fixed before any source/target documents are fetched.
    cold=sorted(asts,key=rank_baseline)
    proved=[];rows=[]
    for name in SOURCE:
        row={"name":name}
        try:
            raw=fetch(name);p=parse_benchmark(raw)
            spec=allowed_table(p)
            solution,checks=solve(spec,cold,sigs)
            row.update({"original_sha256":hashlib.sha256(raw.encode()).hexdigest(),
                "verified_256_cases":solution is not None,"source_checks":checks,
                "proof_program":solution,"grammar":p["allowed_operators"]})
            if solution is not None:proved.append(solution)
        except Exception as e:row["error"]=type(e).__name__+": "+str(e)[:180]
        rows.append(row)
    ordering,weights=learn_order(proved,asts)
    method={"schema":"neumann.q3.formal-bv4-source-policy-first.v1",
        "source":SOURCE,"upstream":"13c8deb68a873635879c9a69bc78caebd340f646",
        "max_candidates":MAX_CANDIDATES,"universal_candidate_count":len(asts),
        "source_proved_count":len(proved),"source_verified_programs":proved,
        "source_records":rows,"learned_feature_weights":weights,
        "learned_ordering":[asts.index(p) for p in ordering],
        "cold_ordering":[asts.index(p) for p in cold],
        "pretarget_source_wall_s":round(time.perf_counter()-started,3),
        "human_written":"SMT formula evaluator, four-bit VM, AST enumeration, feature ranker"}
    method["sha256"]=sha(method)
    pathlib.Path("Q3_FORMAL_SOURCE_FROZEN.json").write_text(json.dumps(method,indent=2))
    print(json.dumps({"source_originals":len(SOURCE),"full_verified":len(proved),
        "candidate_grammar":len(asts),"method_sha256":method["sha256"]},indent=2))
    return method

def target_only():
    import time
    start=time.perf_counter()
    method=json.loads(pathlib.Path("Q3_FORMAL_SOURCE_FROZEN.json").read_text())
    sig=method.pop("sha256")
    if sha(method)!=sig:raise ValueError("SOURCE_TAMPERING")
    if method["source"]!=SOURCE or method["max_candidates"]!=MAX_CANDIDATES:
        raise ValueError("UNTRUSTED_SOURCE_POLICY")
    print("FROZEN_METHOD_BEFORE_ANY_TARGET_DATA",sig)
    asts,sigs=library()
    if len(asts)!=method["universal_candidate_count"]:
        raise ValueError("CANDIDATE_GRAMMAR_DRIFT")
    learned=[asts[i] for i in method["learned_ordering"]]
    cold=[asts[i] for i in method["cold_ordering"]]
    out=[]
    # Candidate/logic same, only order differs; full 256 input proof per task.
    for name in TARGET:
        row={"name":name}
        try:
            raw=fetch(name);p=parse_benchmark(raw)
            spec=allowed_table(p)
            row["original_sha256"]=hashlib.sha256(raw.encode()).hexdigest()
            for key,search in (("learned",learned),("strong_cold",cold)):
                begin=time.perf_counter_ns()
                hit,n=solve(spec,search,sigs)
                row[key]={"proved":hit is not None,
                          "checks":n,"search_ms":round((time.perf_counter_ns()-begin)/1e6,5),
                          "ast":hit}
        except Exception as e:row["error"]=type(e).__name__+": "+str(e)[:180]
        out.append(row)
    summary={
      key:{"proved":sum(bool(r.get(key,{}).get("proved")) for r in out),
          "candidate_checks":sum(r.get(key,{}).get("checks",0) for r in out),
          "search_ms":round(sum(r.get(key,{}).get("search_ms",0) for r in out),4)}
      for key in ("learned","strong_cold")}
    result={"schema":"neumann.q3.independent-author-formal-bv4-target-first.v1",
            "upstream":"13c8deb68a873635879c9a69bc78caebd340f646",
            "source_method_sha256":sig,"target_registry":TARGET,
            "full_semantic_input_count_per_task":256,
            "target_errors":sum("error" in x for x in out),
            "summary":summary,"target_records":out,
            "target_wall_s":round(time.perf_counter()-start,3),
            "interpretation":"full exhaustive 4-bit specs; all AST operators human-coded; scoped test of learned candidate-order transfer, not global autonomous invention"}
    pathlib.Path("Q3_FORMAL_TARGET_FIRST.json").write_text(json.dumps(result,indent=2))
    print(json.dumps({"targets":len(TARGET),"source_sha256":sig,
                     "errors":result["target_errors"],
                     "summary":summary,"wall_s":result["target_wall_s"]},indent=2))
    return result

if __name__=="__main__":
    if len(sys.argv)!=2 or sys.argv[1] not in ("source","target"):
        raise SystemExit("USAGE: source OR target")
    if sys.argv[1]=="source":source_only()
    else:target_only()
