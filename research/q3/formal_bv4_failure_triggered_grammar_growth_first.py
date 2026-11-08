"""Q3 METHOD-GROWTH on NEW untouched formal 4-bit inversion problems.

Detect inability of bounded grammar to satisfy the *formal* 256-input
constraint, then expand executable expression DAGs by type-preserving
composition and observational equivalence deduplication.

The growth algorithm, depth, cap, operators and interpreter are HUMAN-WRITTEN.
Global Q3 remains OPEN. This tests whether growth recovers functions
previously unreachable to a fixed grammar; matched larger-grammar cold
baseline must always receive identical candidate language.
"""
from __future__ import annotations
import collections,hashlib,json,pathlib,time
import formal_bv4_zeroarity_second_unopened_first as fixed

base=fixed.base
TARGET=[f"find_inv_{relation}_{op}_4bit.sl"
        for relation in ("bvslt","bvule") for op in base.OPS]
assert len(TARGET)==32 and len(set(TARGET))==32
assert set(TARGET).isdisjoint(base.SOURCE+base.TARGET+fixed.TARGET)
SOURCE_METHOD_PATH=fixed.SOURCE_METHOD_PATH
MAX_GRAMMAR_CANDIDATES=14000

def enlarge(asts,sigs):
    """Type safe closure of known 4-bit VM nodes; no gold-dependent choice."""
    dedup={signature:ast for ast,signature in sigs.items()}
    additions=[]
    seed=[p for p in asts if p[0] in ("s","t","lit")]
    ordered=sorted(asts,key=base.rank_baseline)
    def add(p):
        if p in sigs:return
        if len(sigs)>=MAX_GRAMMAR_CANDIDATES:return
        value=base.bitvector_signature(p,sigs)
        if value in dedup:return
        sigs[p]=value;dedup[value]=p;additions.append(p)
    for p in ordered:
        if len(sigs)>=MAX_GRAMMAR_CANDIDATES:break
        for unary in ("bvnot","bvneg"):
            add((unary,p))
        for b in seed:
            for op in ("bvadd","bvsub","bvand","bvor","bvlshr","bvshl"):
                add((op,p,b))
                add((op,b,p))
                if len(sigs)>=MAX_GRAMMAR_CANDIDATES:break
            if len(sigs)>=MAX_GRAMMAR_CANDIDATES:break
    # Original syntax always remains; order grows, no deleted source programs.
    return additions,sigs

def run():
    tstart=time.perf_counter()
    source,source_hash=fixed.load_source_method()
    old,sigs=base.library()
    if len(old)!=source["universal_candidate_count"]:
        raise ValueError("FROZEN_OLD_LANGUAGE_CHANGED")
    oldcold=sorted(old,key=base.rank_baseline)
    t=time.perf_counter_ns()
    extra,sigs=enlarge(old,sigs)
    grow_ms=(time.perf_counter_ns()-t)/1e6
    enlarged=old+extra
    fullcold=sorted(enlarged,key=base.rank_baseline)
    # Preserve exactly equal expression language in growing and full arms.
    print("GRAMMAR_FROZEN_BEFORE_TARGET",source_hash,"old",len(old),
          "growth",len(extra),"full",len(enlarged))
    rows=[]
    for name in TARGET:
        rec={"id":name}
        try:
            text=base.fetch(name)
            spec=base.allowed_table(base.parse_benchmark(text))
            rec["source_sha256"]=hashlib.sha256(text.encode()).hexdigest()
            found_old,n_old=base.solve(spec,oldcold,sigs)
            found_full,n_full=base.solve(spec,fullcold,sigs)
            # Degraded-safe: only enlarge on actual model-class failure.
            if found_old is not None:
                found_grow=found_old; n_grow=n_old;why="OLD_PROGRAM_VALID"
            else:
                added=sorted(extra,key=base.rank_baseline)
                found_new,n_more=base.solve(spec,added,sigs)
                found_grow=found_new
                n_grow=n_old+n_more
                why="GROW_AFTER_PROVEN_OLD_GRAMMAR_FAILURE"
            rec.update({"old_fixed":{"proved":found_old is not None,
                                   "candidate_checks":n_old,"ast":found_old},
                       "full_cold_large":{"proved":found_full is not None,
                                   "candidate_checks":n_full,"ast":found_full},
                       "failure_triggered_growth":{"proved":found_grow is not None,
                                   "candidate_checks":n_grow,"ast":found_grow,
                                   "decision":why}})
        except Exception as e:
            rec["error"]=type(e).__name__+": "+str(e)[:190]
        rows.append(rec)
    arms=("old_fixed","full_cold_large","failure_triggered_growth")
    result={"schema":"neumann.q3.source-frozen-formal-bv4-method-growth-original-first.v1",
        "formal_upstream":"13c8deb68a873635879c9a69bc78caebd340f646",
        "prior_source_policy_sha256":source_hash,
        "target_registry":TARGET,"verified_inputs_per_problem":256,
        "old_grammar_size":len(old),"generated_new_expressions":len(extra),
        "full_grammar_size":len(enlarged),"grammar_growth_time_ms":round(grow_ms,5),
        "errors":sum("error" in r for r in rows),
        "summary":{a:{"full_spec_proved":sum(int(r.get(a,{}).get("proved",False)) for r in rows),
                      "program_checks":sum(r.get(a,{}).get("candidate_checks",0) for r in rows)}
                   for a in arms},
        "records":rows,"total_wall_s":round(time.perf_counter()-tstart,4),
        "limits":"Human-coded grammar closure, max depth/cap and algebra. Improvement is representational (if any), not superiority to same-language classical search."}
    pathlib.Path("Q3_FORMAL_GRAMMAR_GROWTH_NEW_FIRST.json").write_text(json.dumps(result,indent=2))
    print(json.dumps({"originals":len(TARGET),"errors":result["errors"],
      "old":len(old),"new_expressions":len(extra),"summary":result["summary"],
      "grammar_growth_ms":result["grammar_growth_time_ms"]},indent=2))
    return result

if __name__=="__main__":run()
