"""Q3 REFLECTIVE METHOD REPAIR:
A source-learned constructor from 5 verified programs fixed BIT(0), but
another independently verified original requires BIT(3).
Automatically anti-unify the *constructor itself* with the new program AST
and admit a typed guard-index hole. Then apply unchanged general VM to a
third untouched cohort. All core machinery remains HUMAN IMPLEMENTED.
"""
from __future__ import annotations
import hashlib,json,pathlib,time
import source_learned_conditional_meta_constructor as prior
import executable_conditional_graph_external_first as base

PREV_A="prior_a/Q3_CONDITIONAL_GRAPH_EXTERNAL_FIRST.json"
PREV_B="prior_b/Q3_LEARNED_META_CONSTRUCTOR_NEW_ORIGINAL_FIRST.json"
TARGET_IDS=[f"PRE_{i}_100" for i in range(1,25)]
assert len(TARGET_IDS)==24
NUM_HOLDOUT=32

def canonical(x):return json.dumps(x,separators=(",",":"),sort_keys=True)
def sha(x):return hashlib.sha256(canonical(x).encode()).hexdigest()

def extract_source_experience(archive_a,archive_b):
    fixed=prior.learn_method_from_prior(archive_a)
    if archive_b.get("target_ids")!=prior.NEW_IDS or archive_b.get("source_errors")!=0:
        raise ValueError("BAD_SECOND_INDEPENDENT_ORIGINAL_SOURCE")
    latest=[]
    for r in archive_b["rows"]:
        v=r.get("cold_full",{})
        score=v.get("score",{})
        p=v.get("program_ast")
        if (score.get("exact") is True and score.get("n")==NUM_HOLDOUT and
            isinstance(p,list) and p[0]=="ite"):
            latest.append((r["task_id"],p))
    if len(latest)<2:raise ValueError("INSUFFICIENT_NEW_SOURCE_COUNTEREXAMPLES")
    method_pattern=fixed["pattern"]
    for ident,ast in latest:
        method_pattern=prior.generalize(method_pattern,ast,{})
    if method_pattern!=["ite",["bit",{"hole":0}],{"hole":1},{"hole":2}]:
        raise ValueError("REFLECTIVE_META_GRAMMAR_NOT_DISCOVERED")
    guards=[]
    for arr in (archive_a["rows"],archive_b["rows"]):
        for rec in arr:
            inp=rec.get("guard_expansion") or rec.get("cold_full")
            if not inp:continue
            if inp.get("heldout",{}).get("exact") is True:
                p=inp.get("synthesis",{}).get("ast")
            elif inp.get("score",{}).get("exact") is True:
                p=inp.get("program_ast")
            else:continue
            if isinstance(p,list) and p[0]=="ite" and p[1][0]=="bit":
                if p[1][1] not in guards:guards.append(p[1][1])
    rule={"kind":"ReflectivelyGeneralizedProgramConstructor",
          "template":method_pattern,"holes":[0,1,2],
          "remembered_guard_values":guards,
          "source_a_programs":fixed["source_original_ids"],
          "new_verified_counterexample_programs":[x[0] for x in latest],
          "human_search_adapter":True,"human_primitives_unchanged":True}
    rule["fingerprint"]=sha(rule)
    return fixed,rule

def solve_for_guards(rule,train,bit_indices):
    t=time.perf_counter()
    xs=[x for x,y in train];ys=[y for x,y in train]
    lib=base.graph_library(xs)
    hits=[];comparisons=len(lib)
    for bit in bit_indices:
        gate=["bit",bit]
        a=[i for i,x in enumerate(xs) if base.check_guard(gate,x)]
        b=[i for i,x in enumerate(xs) if not base.check_guard(gate,x)]
        if not a or not b:continue
        fits_a=[p for p,s in lib if all(s[i]==ys[i] for i in a)]
        fits_b=[p for p,s in lib if all(s[i]==ys[i] for i in b)]
        comparisons+=2*len(lib)
        if not fits_a or not fits_b:continue
        p=min(fits_a,key=lambda x:(base.size(x),str(x)))
        q=min(fits_b,key=lambda x:(base.size(x),str(x)))
        ast=["ite",gate,p,q]
        if all(base.run(ast,x)==y for x,y in train):
            rank=base.size(ast)+10/min(len(a),len(b))
            hits.append((rank,canonical(ast),ast,bit))
    if not hits:
        return {"status":"ABSTAIN_NO_SOURCE_CONSISTENT_METHOD",
                "ast":None,"checks":comparisons,
                "ms":round((time.perf_counter()-t)*1000,5)}
    _,_,ast,bit=min(hits)
    return {"status":"GENERATED_FROM_REFLECTIVE_META_GRAMMAR",
            "ast":ast,"selected_guard_bit":bit,"checks":comparisons,
            "ms":round((time.perf_counter()-t)*1000,5)}

def run_experiment():
    start=time.perf_counter()
    a=json.loads(pathlib.Path(PREV_A).read_text())
    b=json.loads(pathlib.Path(PREV_B).read_text())
    meta_start=time.perf_counter()
    old,expanded=extract_source_experience(a,b)
    meta_ms=round((time.perf_counter()-meta_start)*1000,5)
    frozen={"schema":"neumann.q3.method-repair.v1","source_a_run":42370828681,
            "source_b_run":42371171010,
            "old_method":old,"revised_method":expanded,"meta_learning_ms":meta_ms}
    pathlib.Path("Q3_REFLECTIVE_REPAIR_FROZEN_BEFORE_TARGET.json").write_text(json.dumps(frozen,indent=2))
    print("FROZEN_REFLECTIVE_METHOD",expanded["fingerprint"])
    rows=[]
    old_bits=[old["pattern"][1][1]]
    newer_bits=expanded["remembered_guard_values"]
    for ident in TARGET_IDS:
        row={"id":ident}
        try:
            data=base.get_original(ident)
            train,test=base.source_split(data)
            row["input_data_sha256"]=sha(data);row["published_n"]=len(data)
            row["train_n"]=len(train);row["heldout_n"]=len(test)
            direct=base.synthesize(train,allow_guard=True)
            pold=solve_for_guards(old,train,old_bits)
            pnew=solve_for_guards(expanded,train,newer_bits)
            hybrid=pnew if pnew["ast"] is not None else direct
            for key,r in (("cold_full",direct),("old_fixed_method",pold),
                          ("reflexively_repaired_method",pnew),("new_hybrid",hybrid)):
                ast=r["ast"]
                row[key]={"status":r["status"],"model":ast,
                          "score":base.heldout_score(ast,test),
                          "checks":r.get("checks",r.get("candidate_checks",0)),
                          "discover_ms":r.get("ms",0)}
            row["hybrid_actual_checks"]=pnew["checks"]+(direct["candidate_checks"] if pnew["ast"] is None else 0)
            row["hybrid_actual_ms"]=pnew["ms"]+(direct["ms"] if pnew["ast"] is None else 0)
        except Exception as e:
            row["error"]=type(e).__name__+": "+str(e)[:160]
        rows.append(row)
    arms=("cold_full","old_fixed_method","reflexively_repaired_method","new_hybrid")
    out={"schema":"neumann.q3.reflective-generative-method-independent-third-first.v1",
         "source_a_run":42370828681,"source_b_run":42371171010,
         "upstream_commit":base.UPSTREAM,"meta_method_hash":expanded["fingerprint"],
         "source_induced_guard_values":newer_bits,"target_ids":TARGET_IDS,
         "source_errors":sum(int("error" in r) for r in rows),
         "rows":rows,
         "summary":{k:{"exact_originals":sum(int(r.get(k,{}).get("score",{}).get("exact",False)) for r in rows),
                       "submitted":sum(int(r.get(k,{}).get("score",{}).get("submitted",False)) for r in rows),
                       "candidate_checks":sum(r.get(k,{}).get("checks",0) for r in rows),
                       "discovery_ms":round(sum(r.get(k,{}).get("discover_ms",0) for r in rows),4)}
                    for k in arms},
         "hybrid_actual_checks":sum(r.get("hybrid_actual_checks",0) for r in rows),
         "hybrid_actual_ms":round(sum(r.get("hybrid_actual_ms",0) for r in rows),4),
         "meta_learning_ms":meta_ms,
         "wall_s":round(time.perf_counter()-start,3)}
    pathlib.Path("Q3_REFLECTIVE_REPAIR_NEW_ORIGINAL_FIRST.json").write_text(json.dumps(out,indent=2))
    print(json.dumps({"targets":len(TARGET_IDS),"summary":out["summary"],
                      "source_errors":out["source_errors"],
                      "hybrid_actual_checks":out["hybrid_actual_checks"],
                      "hybrid_actual_ms":out["hybrid_actual_ms"],
                      "meta_learning_ms":meta_ms},indent=2))
    return out

if __name__=="__main__":run_experiment()
