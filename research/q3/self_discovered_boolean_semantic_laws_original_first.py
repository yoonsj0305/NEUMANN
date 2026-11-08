"""Q3 meta-rule invention by FINITE semantic closure and automatic law proof.

SOURCE: earlier externally verified BVSGe original programs used 'or'; Bool
grammar independently supplies NOT and literal constants. From these bases,
enumerate all binary Boolean functions, and derive safe PRUNING invariants
instead of hardcoding AND/OR inclusion laws.

Each discovered law is proven exhaustively over four (A,B) assignments.
Typed generated expressions are executable using only source-licensed NOT/OR
and original comparison atoms. The external original checker independently
verifies all 256 s,t pairs.

TARGET: untouched ic_bvsle and ic_eq 32 official original specs, source rule
SHA frozen before reading ANY target bytes.

NOTE: The semantic closure engine, law shape, typed AST VM, and atom library
are HUMAN-coded. Global Q3 still OPEN even if learned pruning helps.
"""
import hashlib,itertools,json,pathlib,time
import causal_invariant_boolean_existence_first as src

PREV="prior/Q3_BOOLEAN_INVARIANT_SOURCE_FROZEN.json"
METHOD="Q3_AUTO_DISCOVERED_BOOLEAN_METHOD_LAWS_SOURCE.json"
OUTPUT="Q3_AUTO_LAWS_BV_CROSS_RELATION_ORIGINAL_FIRST.json"
TARGET=[f"ic_{rel}_{op}.sl" for rel in ("bvsle","eq") for op in src.base.OPS]
assert len(TARGET)==32 and len(set(TARGET))==32
assert set(TARGET).isdisjoint(src.SOURCE+src.TARGET)

def truth_at(signature,a,b):
    return bool((signature>>(a*2+b))&1)

def symbol_eval(ast,a,b):
    op=ast[0]
    if op=="A":return a
    if op=="B":return b
    if op=="const":return ast[1]
    if op=="not":return not symbol_eval(ast[1],a,b)
    if op=="or":return symbol_eval(ast[1],a,b) or symbol_eval(ast[2],a,b)
    raise ValueError("UNSUPPORTED_META_SYMBOL")

def truth_signature(ast):
    mask=0
    for i,(a,b) in enumerate(itertools.product((False,True),repeat=2)):
        if symbol_eval(ast,a,b):mask|=1<<i
    return mask

def complexity(ast):
    return 1+sum(complexity(x) for x in ast[1:] if isinstance(x,tuple))

def compile_meta_functions():
    """Find 16/16 Boolean binary functions, solely by closing OR/NOT."""
    inventory=[("A",),("B",),("const",False),("const",True)]
    best={truth_signature(ast):ast for ast in inventory}
    first=len(best)
    for depth in range(15):
        previous=list(best.values())
        candidates=[("not",a) for a in previous]
        candidates +=[("or",a,b) for a,b in itertools.product(previous,repeat=2)]
        updates=0
        for ast in candidates:
            value=truth_signature(ast)
            if value not in best or complexity(ast)<complexity(best[value]):
                best[value]=ast;updates+=1
        if len(best)==16 and not updates:break
    if len(best)!=16:raise ValueError("NO_FULL_BOOLEAN_CLOSURE")
    # Direct brute force proof for every discovered executable expression.
    for value,ast in best.items():
        assert truth_signature(ast)==value
    return best,first

def applies_law(name,f,a,b):
    z=truth_at(f,a,b)
    if name=="Z_SUBSET_A":return not z or a
    if name=="A_SUBSET_Z":return not a or z
    if name=="Z_SUBSET_NOT_A":return not z or not a
    if name=="NOT_A_SUBSET_Z":return a or z
    if name=="Z_SUBSET_B":return not z or b
    if name=="B_SUBSET_Z":return not b or z
    if name=="Z_SUBSET_NOT_B":return not z or not b
    if name=="NOT_B_SUBSET_Z":return b or z
    raise ValueError("UNKNOWN_RELATION")

LAW_NAMES=["Z_SUBSET_A","A_SUBSET_Z","Z_SUBSET_NOT_A","NOT_A_SUBSET_Z",
           "Z_SUBSET_B","B_SUBSET_Z","Z_SUBSET_NOT_B","NOT_B_SUBSET_Z"]

def prove_laws(f):
    """Law discovery is by exhaustive semantics, not named AND/OR mapping."""
    return [name for name in LAW_NAMES if all(
        applies_law(name,f,a,b) for a,b in
        itertools.product((False,True),repeat=2))]

def instantiate(ast,A,B):
    op=ast[0]
    if op=="A":return A
    if op=="B":return B
    if op=="const":return ("const",ast[1])
    if op=="not":return ("not",instantiate(ast[1],A,B))
    if op=="or":return ("or",instantiate(ast[1],A,B),
                               instantiate(ast[2],A,B))
    raise ValueError("BAD_GENERATED_META_PROGRAM")

def mask_of_function(f,a,b):
    # Generic four-cell truth-table evaluator for two predicate masks.
    out=0;na=src.FULL^a;nb=src.FULL^b
    if f&1:out |=na&nb
    if f&2:out |=na&b
    if f&4:out |=a&nb
    if f&8:out |=a&b
    return out

def law_filter(law,y,a):
    if law in ("Z_SUBSET_A","Z_SUBSET_B"):return (y&(~a))==0
    if law in ("A_SUBSET_Z","B_SUBSET_Z"):return (a&(~y))==0
    if law in ("Z_SUBSET_NOT_A","Z_SUBSET_NOT_B"):return (y&a)==0
    if law in ("NOT_A_SUBSET_Z","NOT_B_SUBSET_Z"):return ((src.FULL^a)&~y)==0
    raise ValueError("UNSUPPORTED_LAW")

def fast_search(y,atoms,model,prune):
    """Exact same expression program language for both arms.

    A candidate is removed only when a SOURCE-PROVEN necessary law is
    violated by its operand truth set relative to target truth set.
    """
    started=time.perf_counter_ns();checks=0;skips=0;law_tests=0
    if y==0:return ("const",False),1,0,0,(time.perf_counter_ns()-started)/1e6
    if y==src.FULL:return ("const",True),1,0,0,(time.perf_counter_ns()-started)/1e6
    for p,a in atoms:
        checks+=1
        if a==y:return p,checks,skips,law_tests,(time.perf_counter_ns()-started)/1e6
        checks+=1
        if (src.FULL^a)==y:
            return ("not",p),checks,skips,law_tests,(time.perf_counter_ns()-started)/1e6
    funcs=model["functions"]
    for entry in funcs:
        f=entry["truth_signature"]
        ast=entry["expression"]
        law=entry["proved_laws"] if prune else []
        left=[x for x in law if x.endswith("_A")]
        right=[x for x in law if x.endswith("_B")]
        for A,a in atoms:
            if any(not law_filter(rule,y,a) for rule in left):
                skips+=len(atoms);law_tests+=len(left);continue
            for B,b in atoms:
                if any(not law_filter(rule,y,b) for rule in right):
                    skips+=1;law_tests+=len(right);continue
                checks+=1
                if mask_of_function(f,a,b)==y:
                    p=instantiate(ast,A,B)
                    if not src.independently_check(p,y):
                        raise AssertionError("CLOSURE_PROGRAM_FALSE_POSITIVE")
                    return p,checks,skips,law_tests,(time.perf_counter_ns()-started)/1e6
    return None,checks,skips,law_tests,(time.perf_counter_ns()-started)/1e6

def source_only():
    old=json.loads(pathlib.Path(PREV).read_text())
    signature=old.pop("sha256")
    if src.sha(old)!=signature or old["source_registry"]!=src.SOURCE:
        raise ValueError("UNTRUSTED_SOURCE_FIRST")
    if "or" not in old["enabled_compositions"]:
        raise ValueError("UNLICENSED_SOURCE_GENERATOR_PRIMITIVE")
    allfunc,initial_count=compile_meta_functions()
    functions=[]
    for signature_mask,ast in allfunc.items():
        laws=prove_laws(signature_mask)
        functions.append({
            "truth_signature":signature_mask,
            "expression":ast,
            "proved_laws":laws,
            "program_nodes":complexity(ast)})
    functions.sort(key=lambda x:(x["program_nodes"],x["truth_signature"]))
    result={"schema":"neumann.q3.generative-semantic-law-compiler.v1",
       "source_original_run":42434312622,
       "source_first_sha256":signature,
       "permitted_base_ops":["not","or"],
       "seed_binary_functions":initial_count,
       "functions":functions,
       "all_functions_derived":len(functions),
       "independently_verified_boolean_assignments":4,
       "automatically_proven_pruning_laws":sum(len(f["proved_laws"]) for f in functions),
       "human_implemented":"closure algorithm, Boolean interpreter, list of potential law shapes, 220 atom grammar, candidate search"}
    result["sha256"]=src.sha(result)
    pathlib.Path(METHOD).write_text(json.dumps(result,indent=2))
    print(json.dumps({"generated_functions":len(functions),
        "proven_laws":result["automatically_proven_pruning_laws"],
        "source_method_sha256":result["sha256"]},indent=2))
    return result

def target_only():
    model=json.loads(pathlib.Path(METHOD).read_text())
    digest=model.pop("sha256")
    if src.sha(model)!=digest or model["source_original_run"]!=42434312622:
        raise ValueError("SOURCE_METHOD_MODIFIED")
    print("SOURCE_INVENTED_PROGRAM_LANGUAGE_FROZEN_BEFORE_TARGET",digest)
    prep=time.perf_counter_ns();atoms=src.atom_library()
    atom_ms=(time.perf_counter_ns()-prep)/1e6
    rows=[];beg=time.perf_counter()
    for task in TARGET:
        row={"task_id":task}
        try:
            raw=src.fetch(task)
            start=time.perf_counter_ns()
            y,witness=src.existential_truth(raw)
            witness_ms=(time.perf_counter_ns()-start)/1e6
            row["original_sha256"]=hashlib.sha256(raw.encode()).hexdigest()
            row["role"]=src.semantic_role(y)
            row["positive_pairs"]=y.bit_count()
            row["witness_interpretation_ms"]=round(witness_ms,5)
            row["arms"]={}
            for name,pruned in (("same_language_cold",False),
                                ("automatically_proven_invariant",True)):
                p,c,skips,tests,ms=fast_search(y,atoms,model,pruned)
                row["arms"][name]={"full_256_exact":src.independently_check(p,y),
                    "candidate_checks":c,"proven_safe_skips":skips,
                    "invariant_tests":tests,
                    "search_ms":round(ms,5),"program_ast":p}
                if p and not row["arms"][name]["full_256_exact"]:
                    raise AssertionError("INVALID_PROGRAM")
        except Exception as e:row["error"]=type(e).__name__+": "+str(e)[:190]
        rows.append(row)
    arms=("same_language_cold","automatically_proven_invariant")
    summary={name:{"exact":sum(int(x.get("arms",{}).get(name,{}).get("full_256_exact",False)) for x in rows),
                   "checks":sum(x.get("arms",{}).get(name,{}).get("candidate_checks",0) for x in rows),
                   "search_ms":round(sum(x.get("arms",{}).get(name,{}).get("search_ms",0) for x in rows),5)}
             for name in arms}
    result={"schema":"neumann.q3.semantic-rule-invention-cross-operator-new-original-first.v1",
        "source_compiler_sha256":digest,"target_registry":TARGET,
        "source_original_run":42434312622,
        "full_input_pairs_per_original":256,
        "type_checked_candidate_atom_count":len(atoms),
        "shared_language_boolean_function_count":len(model["functions"]),
        "source_program_compile_ms":round(atom_ms,5),
        "total_spec_interpretation_ms":round(sum(x.get("witness_interpretation_ms",0) for x in rows),5),
        "summary":summary,"errors":sum("error" in row for row in rows),
        "rows":rows,"wall_s":round(time.perf_counter()-beg,3),
        "limit":"Proof-guided Boolean-method closure inferred from source OR and NOT, but generic closure and candidate law templates are human-coded; same expressive grammar provided to strong classical."}
    pathlib.Path(OUTPUT).write_text(json.dumps(result,indent=2))
    print(json.dumps({"tasks":len(TARGET),"errors":result["errors"],
        "functions":len(model["functions"]),
        "atom_count":len(atoms),"results":summary,
        "preprocessing_ms":result["total_spec_interpretation_ms"]},indent=2))
    return result

if __name__=="__main__":
    import sys
    if sys.argv[1:]==["source"]:source_only()
    elif sys.argv[1:]==["target"]:target_only()
    else:raise SystemExit("source|target")
