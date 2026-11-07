"""Q3 follow-up: learn a program-generating grammar FROM previously source-frozen
verified ORIGINAL programs, then test a new source-unopened cohort. Not a
claim that Python VM, graph search or antiunification were self-invented.
"""
from __future__ import annotations
import hashlib,json,pathlib,time
import executable_conditional_graph_external_first as base

PREVIOUS_ARTIFACT="Q3_CONDITIONAL_GRAPH_EXTERNAL_FIRST.json"
PRIOR_RUN=42370828681
NEW_IDS=[f"PRE_{i}_100" for i in range(54,78)]
assert len(NEW_IDS)==24
EXPECTED_PREVIOUS_IDS=[f"PRE_{i}_100" for i in range(30,54)]
HELDOUT=32

def encode(v):
    return json.dumps(v,sort_keys=True,separators=(",",":"))
def digest(v):
    return hashlib.sha256(encode(v).encode()).hexdigest()

def generalize(a,b,holes):
    if a==b:return a
    if type(a) in (list,tuple) and type(a)==type(b) and len(a)==len(b) and a and a[0]==b[0]:
        return [generalize(u,v,holes) for u,v in zip(a,b)]
    pair=(encode(a),encode(b))
    if pair not in holes:holes[pair]=len(holes)
    return {"hole":holes[pair]}

def learn_method_from_prior(archive):
    if archive.get("cohort")!=EXPECTED_PREVIOUS_IDS or archive.get("source_errors")!=0:
        raise ValueError("SOURCE_ARTIFACT_PROVENANCE_MISMATCH")
    programs=[];ids=[]
    for row in archive["rows"]:
        gate=row.get("guard_expansion",{})
        out=gate.get("heldout",{})
        synth=gate.get("synthesis",{})
        if (out.get("exact") is True and out.get("n")==HELDOUT and
            synth.get("status")=="SOURCE_DISCOVERED_BRANCH_GRAPH"):
            programs.append(synth["ast"])
            ids.append(row["id"])
    if len(programs)<3:raise ValueError("NOT_ENOUGH_VERIFIED_SOURCE_PROGRAMS")
    pattern=programs[0]
    for p in programs[1:]:
        holes={}
        pattern=generalize(pattern,p,holes)
    # Safety contract: no operation-specific source rule is hand-installed.
    # The universal adapter only knows how to bind the template output
    # when it is a proved branch with holes in both branch functions.
    if not (type(pattern)==list and len(pattern)==4 and pattern[0]=="ite" and
            type(pattern[1])==list and pattern[1][0] in ("bit","eq") and
            pattern[2]=={"hole":0} and pattern[3]=={"hole":1}):
        raise ValueError("SOURCE_DID_NOT_INDUCE_SUPPORTED_NEW_METHOD")
    method={"kind":"LearnedExecutableConditionalGraphConstructor",
            "pattern":pattern,"source_original_ids":ids,
            "source_program_hashes":[digest(x) for x in programs],
            "prior_verified_original_holdout_per_program":HELDOUT,
            "human_written_universal_adapter":True}
    method["content_hash"]=digest(method)
    return method

def apply_learned_method(method,train):
    t=time.perf_counter()
    pat=method["pattern"]
    xs=[x for x,y in train];ys=[y for x,y in train]
    lib=base.graph_library(xs)
    guard=pat[1]
    aidx=[i for i,x in enumerate(xs) if base.check_guard(guard,x)]
    bidx=[i for i,x in enumerate(xs) if not base.check_guard(guard,x)]
    if not aidx or not bidx:
        return {"ast":None,"status":"ABSTAIN_UNSUPPORTED_PARTITION",
                "candidate_checks":len(lib),"ms":round((time.perf_counter()-t)*1e3,5)}
    pa=[p for p,s in lib if all(s[i]==ys[i] for i in aidx)]
    pb=[p for p,s in lib if all(s[i]==ys[i] for i in bidx)]
    if pa and pb:
        p=min(pa,key=lambda q:(base.size(q),str(q)))
        q=min(pb,key=lambda q:(base.size(q),str(q)))
        answer=["ite",guard,p,q]
        if all(base.run(answer,x)==y for x,y in train):
            return {"ast":answer,"status":"SOURCE_LEARNED_META_CONSTRUCTOR",
                    "branch_sizes":[len(aidx),len(bidx)],
                    "candidate_checks":2*len(lib),"ms":round((time.perf_counter()-t)*1e3,5)}
    return {"ast":None,"status":"ABSTAIN_LEARNED_GRAMMAR_INCONSISTENT",
            "candidate_checks":2*len(lib),"ms":round((time.perf_counter()-t)*1e3,5)}

def run_cohort():
    start=time.perf_counter()
    source=json.loads(pathlib.Path("prior",PREVIOUS_ARTIFACT).read_text())
    learning_start=time.perf_counter()
    method=learn_method_from_prior(source)
    learn_ms=round((time.perf_counter()-learning_start)*1e3,5)
    pathlib.Path("Q3_LEARNED_META_METHOD_BEFORE_NEW_TARGETS.json").write_text(
        json.dumps({"method":method,"learning_ms":learn_ms,"prior_run":PRIOR_RUN},
                   indent=2))
    print("FROZEN_NEW_METHOD_SHA256",method["content_hash"])
    rows=[]
    for task in NEW_IDS:
        rec={"task_id":task}
        try:
            data=base.get_original(task)
            train,test=base.source_split(data)
            rec["source_sha256"]=digest(data)
            rec["published_count"]=len(data)
            rec["train_count"]=len(train);rec["heldout_count"]=len(test)
            cold=base.synthesize(train,allow_guard=True)
            learned=apply_learned_method(method,train)
            # Stronger control is cold full grammar, not the previous
            # restricted no-guard grammar; both have the same expressivity.
            hybrid=learned if learned["ast"] is not None else cold
            for name,sol in (("cold_full",cold),("learned_only",learned),("hybrid",hybrid)):
                rec[name]={"status":sol["status"],"checks":sol["candidate_checks"],
                           "discover_ms":sol["ms"],
                           "score":base.heldout_score(sol["ast"],test),
                           "program_ast":sol["ast"]}
            rec["hybrid_with_fallback_checks"]=(learned["candidate_checks"]+
                 (cold["candidate_checks"] if learned["ast"] is None else 0))
            rec["hybrid_with_fallback_ms"]=(learned["ms"]+
                 (cold["ms"] if learned["ast"] is None else 0))
        except Exception as e:
            rec["error"]=type(e).__name__+": "+str(e)[:200]
        rows.append(rec)
    report={"schema":"neumann.q3.learned-program-constructor-independent-first.v1",
      "upstream":base.UPSTREAM,"source_provenance_run":PRIOR_RUN,
      "source_program_count":len(method["source_original_ids"]),
      "frozen_method_hash":method["content_hash"],"method_learning_ms":learn_ms,
      "target_ids":NEW_IDS,"rows":rows,
      "summary":{
       arm:{"exact_originals":sum(int(r.get(arm,{}).get("score",{}).get("exact",False)) for r in rows),
            "submitted":sum(int(r.get(arm,{}).get("score",{}).get("submitted",False)) for r in rows),
            "candidate_checks":sum(r.get(arm,{}).get("checks",0) for r in rows),
            "discovery_ms":round(sum(r.get(arm,{}).get("discover_ms",0) for r in rows),4)}
       for arm in ("cold_full","learned_only","hybrid")},
      "hybrid_checks_actual":sum(r.get("hybrid_with_fallback_checks",0) for r in rows),
      "hybrid_discovery_ms_actual":round(sum(r.get("hybrid_with_fallback_ms",0) for r in rows),4),
      "source_errors":sum(int("error" in r) for r in rows),
      "total_wall_s":round(time.perf_counter()-start,3)}
    pathlib.Path("Q3_LEARNED_META_CONSTRUCTOR_NEW_ORIGINAL_FIRST.json").write_text(
        json.dumps(report,indent=2))
    print(json.dumps({"source_originals":len(method["source_original_ids"]),
       "target_count":len(NEW_IDS),"summary":report["summary"],
       "hybrid_checks_actual":report["hybrid_checks_actual"],
       "hybrid_discovery_ms_actual":report["hybrid_discovery_ms_actual"],
       "source_errors":report["source_errors"]},indent=2))
    return report

if __name__=="__main__":run_cohort()
