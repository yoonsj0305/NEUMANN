"""Q3 cross-DOMAIN independent original FIRST: typed meta-grammar source growth.

SOURCE: official SyGuS-Comp 2019 PBE-SLIA from_2018 named files.
TARGET: official different euphony numeric files (no semantic name clues).
Grammar and problem examples fetched solely after exact runner/compiler freeze.
Original constraint code never executed. No reference solution read.
Scores are PBE original-heldout only; no general functional correctness proof.
"""
from __future__ import annotations
import hashlib,json,pathlib,time,urllib.request
import typed_cross_domain_meta_engine as eng

UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
ROOT=f"https://raw.githubusercontent.com/SyGuS-Org/benchmarks/{UPSTREAM}/comp/2019/PBE_SLIA_Track"
SOURCE=[
    "bikes.sl","dr-name.sl","firstname.sl","initials.sl","lastname.sl",
    "name-combine.sl","name-combine-2.sl","name-combine-3.sl",
    "name-combine-4.sl","reverse-name.sl",
    "phone.sl","phone-1.sl","phone-2.sl","phone-3.sl","phone-4.sl",
    "phone-5.sl","phone-6.sl","phone-7.sl","phone-8.sl","phone-9.sl","phone-10.sl",
    "univ_1.sl","univ_2.sl","univ_3.sl","univ_4.sl","univ_5.sl",
    "univ_6.sl","univ_7.sl","univ_8.sl","univ_9.sl","univ_10.sl"]
TARGET=[
    "12948338.sl","17212077.sl","19274448.sl","19558979.sl",
    "2171308.sl","23435880.sl","25239569.sl","30732554.sl",
    "31753108.sl","33619752.sl","34801680.sl","35016216.sl",
    "35744094.sl","36462127.sl","37281007.sl","37534494.sl",
    "38664547.sl","38871714.sl","39060015.sl","40498040.sl",
    "41503046.sl","43120683.sl","43606446.sl","44789427.sl"]
assert len(TARGET)==24 and len(set(TARGET))==24
assert len(SOURCE)==31 and len(set(SOURCE))==31

def get_source(grp,name):
    url=f"{ROOT}/{grp}/{name}"
    with urllib.request.urlopen(url,timeout=20) as handle:
        raw=handle.read(150001)
    if len(raw)>150000:raise ValueError("SOURCE_SIZE_LIMIT")
    return raw.decode("utf-8")

def split(examples,min_source=3):
    # Deterministic, source/target output-blind hash; only inputs determine
    # ordering, all input duplicates removed by the safe parser.
    ordered=sorted(examples,key=lambda item:hashlib.sha256(eng.canonical(item[0]).encode()).hexdigest())
    if len(ordered)<min_source+1:raise ValueError("NOT_ENOUGH_INDEPENDENT_EXAMPLES")
    n_holdout=min(2,max(1,len(ordered)//4))
    if len(ordered)-n_holdout<min_source:n_holdout=1
    return ordered[:-n_holdout],ordered[-n_holdout:]

def learn_source():
    st=time.perf_counter_ns();verified=[];rows=[]
    for name in SOURCE:
        rec={"id":name}
        try:
            raw=get_source("from_2018",name)
            task=eng.decode_original(raw)
            train,test=split(task["examples"],min_source=2)
            sol=eng.expression_search(task,train,allow_branch=True)
            proof=eng.score(sol["ast"],test)
            rec.update({"source_git_sha256":hashlib.sha256(raw.encode()).hexdigest(),
                "original_examples":len(task["examples"]),"source_n":len(train),
                "heldout_n":len(test),"synthesis_status":sol["status"],
                "heldout":proof,"source_candidate_checks":sol["checks"],
                "source_search_ms":round(sol["wall_ms"],5),
                "generated_ast":sol["ast"]})
            if proof["exact"] and sol["ast"] is not None and eng.size(sol["ast"])>=3:
                verified.append((name,sol["ast"]))
        except Exception as e:rec["error"]=type(e).__name__+": "+str(e)[:150]
        rows.append(rec)
    rules=eng.learn_templates(verified)
    policy={"schema":"neumann.q3.type-polymorphic-source-metagrammar.v1",
       "provenance_source_group":"from_2018",
       "source_ids":SOURCE,"verified_program_ids":[x[0] for x in verified],
       "learned_productions":rules,
       "human_implemented":"tokenizer, VM, generic typed operator enumeration, antiunifier, S-expression grammar validation",
       "source_elapsed_ms":round((time.perf_counter_ns()-st)/1e6,4)}
    policy["content_sha256"]=eng.sha(policy)
    pathlib.Path("Q3_SOURCE_ONLY_TYPED_META_GRAMMAR_FROZEN.json").write_text(json.dumps(policy,indent=2))
    print("FROZEN_SOURCE_META_GRAMMAR",policy["content_sha256"],
          "SOURCE_VERIFIED",len(verified),"NEW_GRAMMAR_PRODUCTIONS",len(rules))
    return policy,rows

def solve_target(task,train,policy):
    # New reusable constructor may be faster than cold; explicit full
    # classical baseline always runs independently and is never suppressed.
    t=time.perf_counter_ns()
    source=eng.memory_search(policy["learned_productions"],task,train,budget=500)
    cold=eng.expression_search(task,train,allow_branch=False)
    full=eng.expression_search(task,train,allow_branch=True)
    elapsed_ms=(time.perf_counter_ns()-t)/1e6
    if source["ast"] is not None:
        selected=source;origin="memory"
        actual_checks=source["checks"]
        actual_ms=source["wall_ms"]
    else:
        selected=full;origin="full_fallback"
        actual_checks=source["checks"]+full["checks"]
        actual_ms=source["wall_ms"]+full["wall_ms"]
    return {"source_learned":source,"cold_base":cold,"strong_full":full,
            "sequential_hybrid":selected,"hybrid_origin":origin,
            "hybrid_actual_checks":actual_checks,"hybrid_actual_ms":round(actual_ms,5),
            "all_arms_wall_ms":round(elapsed_ms,5)}

def first_external():
    start=time.perf_counter_ns()
    policy,source_rows=learn_source()
    # NOTE first target byte access only AFTER policy is stored and hashed.
    rows=[]
    for name in TARGET:
        rec={"id":name}
        try:
            raw=get_source("euphony",name)
            task=eng.decode_original(raw)
            train,test=split(task["examples"],min_source=3)
            solutions=solve_target(task,train,policy)
            rec.update({"original_sha256":hashlib.sha256(raw.encode()).hexdigest(),
              "original_examples":len(task["examples"]),"source_n":len(train),
              "heldout_n":len(test),"nargs":task["nargs"],
              "grammar_operators":task["ops"],
              "grammar_constants":task["constants"],
              "hybrid_origin":solutions["hybrid_origin"],
              "hybrid_actual_checks":solutions["hybrid_actual_checks"],
              "hybrid_actual_ms":solutions["hybrid_actual_ms"]})
            rec["arms"]={}
            for key in ("source_learned","cold_base","strong_full","sequential_hybrid"):
                s=solutions[key]
                rec["arms"][key]={"status":s["status"],"ast":s["ast"],
                   "source_checks":s["checks"],"search_ms":round(s["wall_ms"],5),
                   "original_heldout":eng.score(s["ast"],test),
                   "train_exact":eng.score(s["ast"],train)["exact"]}
        except Exception as e:
            rec["error"]=type(e).__name__+": "+str(e)[:170]
        rows.append(rec)
    arms=("source_learned","cold_base","strong_full","sequential_hybrid")
    stats={name:{"exact_tasks":sum(int(r.get("arms",{}).get(name,{}).get("original_heldout",{}).get("exact",False)) for r in rows),
                 "submitted":sum(int(r.get("arms",{}).get(name,{}).get("original_heldout",{}).get("submitted",False)) for r in rows),
                 "checks":sum(r.get("arms",{}).get(name,{}).get("source_checks",0) for r in rows),
                 "search_ms":round(sum(r.get("arms",{}).get(name,{}).get("search_ms",0) for r in rows),3)}
           for name in arms}
    report={"schema":"neumann.q3.from-verified-strings-meta-to-other-author-string-first.v1",
       "upstream":UPSTREAM,"source_registry":SOURCE,"target_registry":TARGET,
       "source_rows":source_rows,"frozen_source_method_sha256":policy["content_sha256"],
       "new_source_verified_programs":len(policy["verified_program_ids"]),
       "new_auto_productions":len(policy["learned_productions"]),
       "results":rows,"target_errors":sum(int("error" in x) for x in rows),
       "eligible_target_count":sum(int("arms" in x) for x in rows),
       "summary":stats,
       "actual_hybrid_ms":round(sum(r.get("hybrid_actual_ms",0) for r in rows),3),
       "actual_hybrid_checks":sum(r.get("hybrid_actual_checks",0) for r in rows),
       "source_research_elapsed_ms":policy["source_elapsed_ms"],
       "total_wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
       "limitations":"One or two published original heldout checks per task. Same competition, different input subgroups; do not claim different authors proven. No reference semantics or general correct solutions; no Q3 global PASS."}
    pathlib.Path("Q3_CROSS_DOMAIN_STRING_UNOPENED_FIRST.json").write_text(json.dumps(report,indent=2))
    print(json.dumps({"source_verified":report["new_source_verified_programs"],
       "learned_new_productions":report["new_auto_productions"],
       "eligible_target_count":report["eligible_target_count"],
       "target_errors":report["target_errors"],"results":report["summary"],
       "actual_hybrid_ms":report["actual_hybrid_ms"],
       "source_research_elapsed_ms":report["source_research_elapsed_ms"]},indent=2))
    return report

if __name__=="__main__":first_external()
