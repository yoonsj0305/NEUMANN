"""Q3 source-derived macro from a *new* fully verified original program.

SOURCE: frozen 32-task grammar-growth original FIRST #42432876840.
Extract any 4-bit input-independent subexpressions in previously certified
ASTs that the old grammar could not solve. The new macro is learned, never
provided as a literal by the researcher or a target solution.
TARGET: untouched official inverse groups unsigned> and not-equal (32).
Compare matched-language classical and learned macro-first search.
All macro/interpreter/code logic is HUMAN IMPLEMENTED, Q3 global OPEN.
"""
from __future__ import annotations
import hashlib,json,pathlib,time
import formal_bv4_failure_triggered_grammar_growth_first as grown

base=grown.base
PRIOR="prior/Q3_FORMAL_GRAMMAR_GROWTH_NEW_FIRST.json"
TARGET=[f"find_inv_{relation}_{op}_4bit.sl"
        for relation in ("bvugt","ne") for op in base.OPS]
assert len(TARGET)==32 and len(set(TARGET))==32
assert set(TARGET).isdisjoint(grown.TARGET+base.SOURCE+base.TARGET+
                            grown.fixed.TARGET)

def encode_ast(p):
    return tuple(encode_ast(x) if isinstance(x,list) else x for x in p)

def has_input(p):
    if p[0] in ("s","t"):return True
    return any(has_input(x) for x in p[1:] if isinstance(x,tuple))

def value(p,s,t):
    op=p[0]
    if op=="s":return s
    if op=="t":return t
    if op=="lit":return p[1]
    args=[value(child,s,t) for child in p[1:]]
    return base.bv(op,*args)

def subtrees(p):
    yield p
    for child in p[1:]:
        if isinstance(child,tuple):yield from subtrees(child)

def extract_memory():
    proof=json.loads(pathlib.Path(PRIOR).read_text())
    if proof.get("target_registry")!=grown.TARGET or proof.get("errors")!=0:
        raise ValueError("BAD_SOURCE_ORIGINAL_FIRST_PROVENANCE")
    fresh=[]
    for rec in proof["records"]:
        if (not rec["old_fixed"]["proved"] and
                rec["full_cold_large"]["proved"] and
                rec["full_cold_large"]["ast"]):
            fresh.append((rec["id"],encode_ast(rec["full_cold_large"]["ast"])))
    if not fresh:raise ValueError("NO_VERIFIED_NEW_SOURCE_PROGRAM")
    pool={};new_records=[]
    for ident,ast in fresh:
        for tree in subtrees(ast):
            if has_input(tree):continue
            out=[value(tree,s,t) for s,t in base.PAIRS]
            if len(set(out))!=1:raise AssertionError("NON_CONSTANT_SUBTREE")
            v=out[0]
            if v in (0,7,8):continue
            tree_key=json.dumps(tree)
            if tree_key not in pool:
                pool[tree_key]={"value":v,"macro_ast":tree,
                     "source_id":ident,"verified_256_inputs":True}
    if not pool:raise ValueError("NO_REUSABLE_NEW_SOURCE_MACROS")
    report={"schema":"neumann.q3.externally-proven-source-macro.v1",
            "prior_source_full_domain_run":42432876840,
            "source_new_program_ids":[a for a,b in fresh],
            "source_programs":[b for a,b in fresh],
            "derived_constant_macros":list(pool.values()),
            "human_supplied":"typed AST interpretation, constant-expression detection, candidate-generation operators"}
    report["sha256"]=base.sha(report)
    pathlib.Path("Q3_EXTERNAL_SOURCE_MACRO_FROZEN.json").write_text(json.dumps(report,indent=2))
    print("SOURCE_MACRO_FROZEN_BEFORE_TARGET",report["sha256"],
          "macros",len(report["derived_constant_macros"]))
    return report

def macro_programs(rule):
    # The macro subtree is not replaced with an unlicensed literal.
    # Every emitted candidate uses executable operators of original grammar.
    seed=[("s",),("t",),("lit",0),("lit",7),("lit",8)]
    seen=set();out=[]
    for m in rule["derived_constant_macros"]:
        macro=encode_ast(m["macro_ast"]) if isinstance(m["macro_ast"],list) else m["macro_ast"]
        for other in seed:
            for op in ("bvadd","bvsub","bvand","bvor","bvlshr","bvshl"):
                for p in ((op,other,macro),(op,macro,other)):
                    if p not in seen:
                        seen.add(p);out.append(p)
    return out

def target_run():
    rule=json.loads(pathlib.Path("Q3_EXTERNAL_SOURCE_MACRO_FROZEN.json").read_text())
    signature=rule.pop("sha256")
    if base.sha(rule)!=signature:raise ValueError("SOURCE_RULE_CHANGED")
    if rule["prior_source_full_domain_run"]!=42432876840:
        raise ValueError("SOURCE_RUN_WRONG")
    print("TARGET_ACCESS_AFTER_SOURCE_FROZEN",signature)
    originals,sigs=base.library()
    grown_new,sigs=grown.enlarge(originals,sigs)
    learned=macro_programs(rule)
    for p in learned:
        if p not in sigs:
            sigs[p]=base.bitvector_signature(p,sigs) if all(
               child in sigs for child in p[1:] if isinstance(child,tuple)) else tuple(
                 value(p,s,t) for s,t in base.PAIRS)
    basecold=sorted(originals,key=base.rank_baseline)
    all_lib=list(dict.fromkeys(originals+grown_new+learned))
    matched_cold=sorted(all_lib,key=base.rank_baseline)
    macro_first=list(dict.fromkeys(learned+basecold+grown_new))
    begin=time.perf_counter()
    rows=[]
    for name in TARGET:
        rec={"id":name}
        try:
            source=base.fetch(name)
            spec=base.allowed_table(base.parse_benchmark(source))
            rec["original_sha256"]=hashlib.sha256(source.encode()).hexdigest()
            for label,order in (("fixed_grammar_cold",basecold),
                                ("macro_first",macro_first),
                                ("same_language_full_cold",matched_cold)):
                tick=time.perf_counter_ns()
                ast,c=base.solve(spec,order,sigs)
                rec[label]={"proved":ast is not None,"checks":c,
                    "search_ms":round((time.perf_counter_ns()-tick)/1e6,5),
                    "program":ast,
                    "selected_macro_expression":bool(ast is not None and ast in learned)}
        except Exception as e:rec["error"]=type(e).__name__+": "+str(e)[:160]
        rows.append(rec)
    summary={k:{"full_256_proved":sum(int(r.get(k,{}).get("proved",False)) for r in rows),
                "checks":sum(r.get(k,{}).get("checks",0) for r in rows),
                "search_ms":round(sum(r.get(k,{}).get("search_ms",0) for r in rows),5),
                "direct_macro_solutions":sum(int(r.get(k,{}).get("selected_macro_expression",False)) for r in rows)}
             for k in ("fixed_grammar_cold","macro_first","same_language_full_cold")}
    out={"schema":"neumann.q3.source-extracted-macro-cross-operator-original-first.v1",
         "source_rule_sha256":signature,"new_registry":TARGET,
         "source_proof_run":42432876840,
         "human_interpreter":True,
         "universal_old_count":len(originals),
         "universal_grown_count":len(grown_new),
         "source_macro_generated_count":len(learned),
         "candidate_shared_full_universe":len(all_lib),
         "summary":summary,"errors":sum("error" in r for r in rows),
         "records":rows,"target_wall_s":round(time.perf_counter()-begin,3)}
    pathlib.Path("Q3_MACRO_GENERALIZATION_NEW_ORIGINAL_FIRST.json").write_text(json.dumps(out,indent=2))
    print(json.dumps({"tasks":len(TARGET),"errors":out["errors"],
      "source_macro_count":len(rule["derived_constant_macros"]),
      "new_generated_candidates":len(learned),"summary":summary},indent=2))
    return out

if __name__=="__main__":
    import sys
    if sys.argv[1:]==["source"]:extract_memory()
    elif sys.argv[1:]==["target"]:target_run()
    else:raise SystemExit("usage source|target")
