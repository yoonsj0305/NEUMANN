"""Q3 second untouched formal inverse cohort after generic 0-arity constant fix.

Previous FIRST run 42432369260 is immutable. Download source method and
do not relearn from target. New untouched official 4-bit groups: unsigned
less-than and equality. This narrow parser correction is not a new grammar.
"""
from __future__ import annotations
import hashlib,json,pathlib,time
import formal_bv4_independent_author_original_first as base

BASE_EXPR=base.expr

def interpret_fixed(ast,env,defs,inv_value,depth=0):
    if isinstance(ast,str) and ast in defs:
        params,body=defs[ast]
        if not params:
            return interpret_fixed(body,env,defs,inv_value,depth+1)
    return BASE_EXPR(ast,env,defs,inv_value,depth)

base.expr=interpret_fixed

ORIGINAL_FIRST=42432369260
SOURCE_METHOD_PATH="source_policy/Q3_FORMAL_SOURCE_FROZEN.json"
TARGET=[f"find_inv_{relation}_{op}_4bit.sl"
        for relation in ("bvult","eq") for op in base.OPS]
assert len(TARGET)==32 and len(set(TARGET))==32
assert set(TARGET).isdisjoint(base.SOURCE)
assert set(TARGET).isdisjoint(base.TARGET)

def load_source_method():
    obj=json.loads(pathlib.Path(SOURCE_METHOD_PATH).read_text())
    fingerprint=obj.pop("sha256")
    if base.sha(obj)!=fingerprint:raise ValueError("FROZEN_SOURCE_METHOD_TAMPERED")
    if obj["source"]!=base.SOURCE or obj["max_candidates"]!=base.MAX_CANDIDATES:
        raise ValueError("SOURCE_CONTRACT_MISMATCH")
    return obj,fingerprint

def run():
    start=time.perf_counter()
    source,fp=load_source_method()
    asts,sigs=base.library()
    if len(asts)!=source["universal_candidate_count"]:
        raise ValueError("CANDIDATE_UNIVERSE_DRIFT")
    cold=[asts[i] for i in source["cold_ordering"]]
    learned=[asts[i] for i in source["learned_ordering"]]
    print("FROZEN_BEFORE_ANY_TARGET_BYTES",fp)
    rows=[]
    for name in TARGET:
        rec={"id":name}
        try:
            original=base.fetch(name)
            parsed=base.parse_benchmark(original)
            table=base.allowed_table(parsed)
            rec["original_sha256"]=hashlib.sha256(original.encode()).hexdigest()
            rec["constrained_inputs"]=sum(v!=65535 for v in table)
            for key,order in (("memory_policy",learned),
                              ("strong_cold_same_grammar",cold)):
                t0=time.perf_counter_ns()
                ast,n=base.solve(table,order,sigs)
                rec[key]={"proved":ast is not None,"checks":n,
                   "search_ms":round((time.perf_counter_ns()-t0)/1e6,5),
                   "program":ast}
        except Exception as e:
            rec["error"]=type(e).__name__+": "+str(e)[:180]
        rows.append(rec)
    arms=("memory_policy","strong_cold_same_grammar")
    report={"schema":"neumann.q3.zeroarg-patched-formal-bv4-untouched-second-first.v1",
      "source_first_run":ORIGINAL_FIRST,"source_method_sha256":fp,
      "upstream_commit":"13c8deb68a873635879c9a69bc78caebd340f646",
      "new_registry":TARGET,"full_input_space_per_problem":256,
      "code_change_only":"SMT-LIB zero-arity define-fun atom resolution",
      "summary":{key:{"proved":sum(int(r.get(key,{}).get("proved",False)) for r in rows),
                       "checks":sum(r.get(key,{}).get("checks",0) for r in rows),
                       "search_ms":round(sum(r.get(key,{}).get("search_ms",0) for r in rows),5)}
                 for key in arms},
      "errors":sum("error" in r for r in rows),
      "records":rows,"elapsed_s":round(time.perf_counter()-start,3)}
    pathlib.Path("Q3_FORMAL_SECOND_ORIGINAL_FIRST.json").write_text(json.dumps(report,indent=2))
    print(json.dumps({"targets":len(TARGET),"source_method_sha256":fp,
      "summary":report["summary"],"errors":report["errors"]},indent=2))
    return report

if __name__=="__main__":run()
