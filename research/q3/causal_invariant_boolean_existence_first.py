"""Q3 proof-guided causal invariants -> boolean method synthesis.

Official external SyGuS invertibility-CONDITION problems, rather than prior
inverse witness programs. Source 16 bvsge; target NEW 32 bvslt + bvuge.
Semantic procedure discovers necessary/sufficient TRUE-SET relations between
candidate predicates and the existential witness function.

Each original contract quantifies 4-bit x, s, t: SC(s,t) iff some x satisfies
case(x,s,t). We compile this from the ORIGINAL SyGuS formula, not an oracle.
Published reference solutions are never fetched or used.

The predicate VM, finite-state quantifier elimination, term grammar,
invariant-ranking policy and budget remain HUMAN CODE. Do not label global Q3.
"""
from __future__ import annotations
import hashlib,itertools,json,pathlib,time,urllib.request
import formal_bv4_zeroarity_second_unopened_first as zero
base=zero.base

ROOT="https://raw.githubusercontent.com/SyGuS-Org/benchmarks/13c8deb68a873635879c9a69bc78caebd340f646/comp/2019/General_Track/bv-invertibility-conditions/"
SOURCE=[f"ic_bvsge_{op}.sl" for op in base.OPS]
TARGET=[f"ic_{cmp}_{op}.sl" for cmp in ("bvslt","bvuge") for op in base.OPS]
assert len(SOURCE)==16 and len(TARGET)==32 and not set(SOURCE)&set(TARGET)
FULL=(1<<256)-1
MAX_ATOMS=220
FROZEN="Q3_CAUSAL_SOURCE_INVARIANT_METHOD_FROZEN.json"
RAW_ROWS="Q3_CAUSAL_TARGET_ORIGINAL_FIRST.json"

def canon(x):return json.dumps(x,sort_keys=True,separators=(",",":"))
def sha(x):return hashlib.sha256(canon(x).encode()).hexdigest()

def fetch(name):
    with urllib.request.urlopen(ROOT+name,timeout=25) as h: raw=h.read(150001)
    if len(raw)>150000:raise ValueError("OVERSIZE")
    return raw.decode()

def flatten_or(form):
    if isinstance(form,list) and form and form[0]=="or":
        ans=[]
        for child in form[1:]:ans+=flatten_or(child)
        return ans
    return [form]

def original_contract(raw):
    forms=base.parse_smt(raw)
    fs=[r for r in forms if r and r[0]=="synth-fun"]
    cs=[r[1] for r in forms if r and r[0]=="constraint"]
    if len(fs)!=1 or len(cs)!=1 or fs[0][1]!="SC":
        raise ValueError("WRONG_ORIGINAL_CONTRACT")
    eq=cs[0]
    if not isinstance(eq,list) or len(eq)!=3 or eq[0]!="=":raise ValueError("NOT_EQUIVALENCE")
    rhs=["SC","s","t"]
    if eq[1]==rhs:or_expr=eq[2]
    elif eq[2]==rhs:or_expr=eq[1]
    else:raise ValueError("MISSING_SC_IN_ORIGINAL_CONSTRAINT")
    clauses=flatten_or(or_expr)
    if len(clauses)!=16 or not all(
        isinstance(x,list) and len(x)==4 and
        x[0]=="case" and x[2:]==["s","t"] for x in clauses):
        raise ValueError("NOT_A_COMPLETE_16_WITNESS_OR")
    witness=sorted(int(x[1][2:],16) for x in clauses)
    if witness!=list(range(16)):raise ValueError("WITNESS_DOMAIN_INCOMPLETE")
    definitions={}
    for row in forms:
        if row and row[0]=="define-fun":
            if len(row)!=5:raise ValueError("MALFORMED_DEFINE")
            definitions[row[1]]=(row[2],row[4])
    if "case" not in definitions:raise ValueError("NO_CASE_DEFINITION")
    if fs[0][3]!="Bool":raise ValueError("NOT_BOOLEAN_OUTPUT")
    return definitions,clauses

def existential_truth(raw):
    defs,clauses=original_contract(raw)
    truth=0;calls=0
    for i,(s,t) in enumerate(base.PAIRS):
        env={"s":s,"t":t}
        solved=False
        for case in clauses:
            calls+=1
            if base.expr(case,env,defs,0):
                solved=True;break
        if solved:truth|=(1<<i)
    return truth,calls

def atom_library():
    """All candidate arms receive this exact same human-coded typed grammar."""
    s=("s",);t=("t",)
    bases=[s,t,("lit",0),("lit",7),("lit",8)]
    terms=bases+[("bvnot",s),("bvneg",s),("bvnot",t),("bvneg",t),
                 ("bvadd",s,t),("bvadd",t,s),("bvsub",s,t),("bvsub",t,s),
                 ("bvand",s,t),("bvor",s,t),
                 ("bvshl",s,("lit",7)),("bvlshr",s,("lit",7))]
    # Ensure bitvector terms are legal grammar productions for all sources.
    terms=list(dict.fromkeys(terms))
    tvals={p:base.bitvector_signature(p,{}) for p in bases}
    for p in terms:
        if p in tvals:continue
        tvals[p]=tuple(base.value(p,a,b) if hasattr(base,"value") else simple(p,a,b)
                       for a,b in base.PAIRS)
    atoms=[];seen={}
    for op in ("=","bvult","bvslt","bvuge","bvsge"):
        for left,right in itertools.product(terms,repeat=2):
            vl=tvals[left];vr=tvals[right]
            mask=0
            for i,(a,b) in enumerate(zip(vl,vr)):
                if truth_pred(op,a,b):mask|=1<<i
            if mask not in seen:
                p=(op,left,right)
                seen[mask]=p
                atoms.append((p,mask))
    atoms.sort(key=lambda item:(n_nodes(item[0]),canon(item[0])))
    return atoms[:MAX_ATOMS]

def simple(p,s,t):
    op=p[0]
    if op=="s":return s
    if op=="t":return t
    if op=="lit":return p[1]
    args=[simple(x,s,t) for x in p[1:]]
    return base.bv(op,*args)

def truth_pred(op,a,b):
    if op=="=":return a==b
    if op=="bvult":return a<b
    if op=="bvuge":return a>=b
    if op=="bvslt":return base.signed(a)<base.signed(b)
    if op=="bvsge":return base.signed(a)>=base.signed(b)
    raise ValueError("UNKNOWN_COMPARISON")

def n_nodes(p):
    return 1+sum(n_nodes(x) for x in p[1:] if isinstance(x,tuple))

def semantic_role(y):
    if y==0:return "ALWAYS_FALSE"
    if y==FULL:return "ALWAYS_TRUE"
    s_independent=all(bool((y>>((s<<4)+t))&1)==bool((y>>((s<<4)+0))&1)
                      for s in range(16) for t in range(16))
    t_independent=all(bool((y>>((s<<4)+t))&1)==bool((y>>((0<<4)+t))&1)
                      for s in range(16) for t in range(16))
    if s_independent:return "ONLY_S"
    if t_independent:return "ONLY_T"
    return "JOINT_S_T"

def normalize(a):
    p,truth=a
    return p,truth

def cold_solve(y,atoms):
    """Strong same-language classical: constants, atom, its NOT,
    then all typed two-atom AND/OR. No source-memorized search order."""
    if y==0:return ("const",False),1
    if y==FULL:return ("const",True),1
    trials=2
    for p,m in atoms:
        trials+=1
        if m==y:return p,trials
        trials+=1
        if (FULL^m)==y:return ("not",p),trials
    for i,(p,m) in enumerate(atoms):
        for q,n in atoms[i+1:]:
            trials+=1
            if m&n==y:return ("and",p,q),trials
            trials+=1
            if m|n==y:return ("or",p,q),trials
    return None,trials

def invariant_solve(y,atoms,recipe):
    """Typed quotient-invariant procedure. Classify candidate truth sets:
    a necessary condition implies Y subset A; sufficient implies A subset Y.
    A pair can match via intersection or union iff these relationships hold.
    The source-program-derived enabled compositions are frozen BEFORE target.
    """
    if y==0:return ("const",False),1,{"causal_role":"ALWAYS_FALSE"}
    if y==FULL:return ("const",True),1,{"causal_role":"ALWAYS_TRUE"}
    checked=2
    for p,m in atoms:
        checked+=1
        if y==m:return p,checked,{"causal_role":"EXACT"}
        checked+=1
        if y==(FULL^m):return ("not",p),checked,{"causal_role":"COMPLEMENT"}
    necessary=[(p,m) for p,m in atoms if (y&(~m))==0]
    sufficient=[(p,m) for p,m in atoms if (m&(~y))==0]
    enabled=recipe["enabled_compositions"]
    if "and" in enabled:
        for i,(p,m) in enumerate(necessary):
            for q,n in necessary[i+1:]:
                checked+=1
                if m&n==y:
                    return ("and",p,q),checked,{"causal_role":"NECESSARY_INTERSECTION",
                        "necessary_n":len(necessary)}
    if "or" in enabled:
        for i,(p,m) in enumerate(sufficient):
            for q,n in sufficient[i+1:]:
                checked+=1
                if m|n==y:
                    return ("or",p,q),checked,{"causal_role":"SUFFICIENT_UNION",
                        "sufficient_n":len(sufficient)}
    return None,checked,{"causal_role":semantic_role(y),
        "necessary_n":len(necessary),"sufficient_n":len(sufficient)}

def value_bool(p,s,t):
    op=p[0]
    if op=="const":return p[1]
    if op=="not":return not value_bool(p[1],s,t)
    if op=="and":return value_bool(p[1],s,t) and value_bool(p[2],s,t)
    if op=="or":return value_bool(p[1],s,t) or value_bool(p[2],s,t)
    return truth_pred(op,simple(p[1],s,t),simple(p[2],s,t))

def independently_check(p,y):
    return p is not None and all(bool((y>>i)&1)==value_bool(p,s,t)
                         for i,(s,t) in enumerate(base.PAIRS))

def learn_source():
    started=time.perf_counter()
    atoms=atom_library();rows=[];proven=[];seen=set()
    for name in SOURCE:
        row={"name":name}
        try:
            raw=fetch(name)
            y,wit=existential_truth(raw)
            p,n=cold_solve(y,atoms)
            verified=independently_check(p,y)
            row.update({"sha256":hashlib.sha256(raw.encode()).hexdigest(),
                "role":semantic_role(y),"true_cases":y.bit_count(),
                "witness_checks":wit,"source_proved":verified,
                "expression":p,"candidate_checks":n})
            if verified:
                proven.append(p)
                seen.update(list_ops(p))
        except Exception as e:
            row["error"]=type(e).__name__+": "+str(e)[:170]
        rows.append(row)
    # Source evidence may constrain the invention of a new search recipe.
    # If no composite rule is certified, graceful degraded full grammar.
    operators=[x for x in ("and","or") if x in seen]
    method={"schema":"neumann.q3.semantic-invariant-compiler-source.v1",
       "source_registry":SOURCE,"upstream":"13c8deb68a873635879c9a69bc78caebd340f646",
       "source_proved":len(proven),"source_records":rows,
       "atomic_feature_count":len(atoms),
       "learned_roles":sorted(set(r.get("role") for r in rows if "role" in r)),
       "enabled_compositions":operators if operators else ["and","or"],
       "default_compositions_used":not bool(operators),
       "human_wrote":"typed compiler, source semantic relation extraction, set-inclusion filter, grammar, role classifier",
       "source_elapsed_s":round(time.perf_counter()-started,4)}
    method["sha256"]=sha(method)
    pathlib.Path("Q3_BOOLEAN_INVARIANT_SOURCE_FROZEN.json").write_text(json.dumps(method,indent=2))
    print(json.dumps({"source_n":len(SOURCE),"source_proved":len(proven),
                      "atom_count":len(atoms),"enabled":method["enabled_compositions"],
                      "source_errors":sum("error" in r for r in rows),
                      "source_sha256":method["sha256"]},indent=2))
    return method

def list_ops(node):
    if not isinstance(node,tuple):return []
    return [node[0]]+sum((list_ops(ch) for ch in node[1:] if isinstance(ch,tuple)),[])

def run_target():
    method=json.loads(pathlib.Path("Q3_BOOLEAN_INVARIANT_SOURCE_FROZEN.json").read_text())
    claimed=method.pop("sha256")
    if sha(method)!=claimed or method["source_registry"]!=SOURCE:
        raise ValueError("UNVERIFIED_FROZEN_SOURCE")
    atoms=atom_library()
    print("SOURCE_METHOD_FROZEN_BEFORE_TARGET",claimed)
    start=time.perf_counter()
    rows=[]
    for name in TARGET:
        row={"name":name}
        try:
            raw=fetch(name)
            y,w=existential_truth(raw)
            row["original_sha256"]=hashlib.sha256(raw.encode()).hexdigest()
            row["causal_input_role"]=semantic_role(y)
            row["positive_inputs"]=y.bit_count()
            t=time.perf_counter_ns()
            naive,c= cold_solve(y,atoms)
            coldms=(time.perf_counter_ns()-t)/1e6
            t=time.perf_counter_ns()
            generated,g,meta=invariant_solve(y,atoms,method)
            genms=(time.perf_counter_ns()-t)/1e6
            row["strong_cold"]={"proved":independently_check(naive,y),
                "checks":c,"elapsed_ms":round(coldms,5),"ast":naive}
            row["causal_invariant"]={"proved":independently_check(generated,y),
                "checks":g,"elapsed_ms":round(genms,5),"ast":generated,
                "semantic_certificate":meta}
            if generated is not None and not independently_check(generated,y):
                raise AssertionError("GENERATED_INVARIANT_NOT_VALID")
        except Exception as e:row["error"]=type(e).__name__+": "+str(e)[:200]
        rows.append(row)
    arms=("strong_cold","causal_invariant")
    summary={arm:{"exact":sum(int(r.get(arm,{}).get("proved",False)) for r in rows),
                  "candidate_checks":sum(r.get(arm,{}).get("checks",0) for r in rows),
                  "search_ms":round(sum(r.get(arm,{}).get("elapsed_ms",0) for r in rows),5)}
             for arm in arms}
    result={"schema":"neumann.q3.invariant-causal-boolean-official-first.v1",
        "upstream_commit":"13c8deb68a873635879c9a69bc78caebd340f646",
        "frozen_source_sha256":claimed,"new_target_registry":TARGET,
        "full_input_pairs_per_task":256,
        "target_errors":sum("error" in r for r in rows),
        "source_recipes":method["enabled_compositions"],
        "summary":summary,"rows":rows,
        "wall_seconds":round(time.perf_counter()-start,4),
        "scope":"4-bit official source and target both from same SyGuS provider, different relational condition tasks; finite typed Boolean grammar human-written; zero global Q3 claim."}
    pathlib.Path("Q3_BOOLEAN_INVARIANT_FRESH_FIRST.json").write_text(json.dumps(result,indent=2))
    print(json.dumps({"total":len(TARGET),"errors":result["target_errors"],
                      "source_sha256":claimed,"results":summary},indent=2))
    return result

if __name__=="__main__":
    import sys
    if sys.argv[1:]==["source"]:learn_source()
    elif sys.argv[1:]==["target"]:run_target()
    else:raise SystemExit("source|target")
