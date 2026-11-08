"""Q3 transfer to external INTEGER source families with algebraic invariants.

No new target contents are fetched before the source policy and algebraic
law certificates are SHA frozen. New official CLIA cohorts:
  - differently named max16..20 originals
  - arraysearch16..20 as negative out-of-family controls
  - array_sum and conditional-program variants as other OOD controls

The 12 source-proven integer max2/3 fold grammar is unchanged. No new
target-specific rules/ops. Fail-closed on unsupported syntax and SAT proofs.
"""
from __future__ import annotations
import hashlib,json,pathlib,time
import z3
import cross_theory_boolean_invariant_to_unbounded_lia_first as prior

METHOD="Q3_INTEGER_ALGEBRAIC_LAWS_SOURCE_ONLY_FROZEN.json"
OUTPUT="Q3_INTEGER_DIVERSE_CO_12_UNSEEN_ORIGINAL_FIRST.json"
PRIOR_POLICY="source_policy/Q3_CROSS_THEORY_INTEGER_SOURCE_POLICY_FROZEN.json"
COHORTS={
    "alternate_max_name":[f"max{i}.sl" for i in range(16,21)],
    "array_search_ood":[f"arraysearch{i}.sl" for i in range(16,21)],
    "other_clia_ood":[
        "jmbl_fg_array_sum_2_5.sl",
        "jmbl_fg_array_sum_3_5.sl",
        "jmbl_fg_mpg_guard2.sl",
        "jmbl_fg_mpg_ite2.sl"]}
TARGET=[x for rows in COHORTS.values() for x in rows]
assert len(TARGET)==14 and len(set(TARGET))==14
assert set(TARGET).isdisjoint(prior.SOURCE+prior.TARGET)

def prior_policy():
    model=json.loads(pathlib.Path(PRIOR_POLICY).read_text())
    digest=model.pop("sha256")
    if prior.sha(model)!=digest or model["integer_source_names"]!=prior.SOURCE:
        raise ValueError("CHANGED_INTEGER_SOURCE")
    if model["frozen_boolean_source"]!=prior.load_prior():
        raise ValueError("CHANGED_BOOLEAN_SOURCE")
    return model,digest

def learned_bifunction(a,b,variant):
    guard,order=variant
    relations={
        "=":a==b, "distinct":a!=b,
        "<":a<b, "<=":a<=b, ">":a>b, ">=":a>=b}
    predicate=relations[guard]
    return z3.If(predicate,a,b) if order=="left" else z3.If(predicate,b,a)

def source_law_discovery():
    model,digest=prior_policy()
    chosen=tuple(model["learned_fold_constructor"])
    a,b,c,u,v=z3.Ints("a b c u v")
    g=lambda x,y:learned_bifunction(x,y,chosen)
    hypotheses={
      "commutative":g(a,b)==g(b,a),
      "associative":g(g(a,b),c)==g(a,g(b,c)),
      "idempotent":g(a,a)==a,
      "selective":z3.Or(g(a,b)==a,g(a,b)==b),
      "lower_bound":z3.And(g(a,b)>=a,g(a,b)>=b),
      "monotone":z3.Implies(z3.And(a<=u,b<=v),g(a,b)<=g(u,v)),
      "identity_zero":g(a,z3.IntVal(0))==a}
    results=[]
    for name,p in hypotheses.items():
        solver=z3.Solver()
        solver.set(timeout=6000)
        solver.add(z3.Not(p))
        ans=solver.check()
        results.append({"candidate_property":name,
              "disposition":str(ans),
              "proved":ans==z3.unsat,
              "counterexample":str(solver.model())[:200] if ans==z3.sat else None})
    verified=[x["candidate_property"] for x in results if x["proved"]]
    if not all(x in verified for x in ("commutative","associative","idempotent","selective","lower_bound","monotone")):
        raise ValueError("NO_GENERIC_INTEGER_FOLD_LAWS")
    if "identity_zero" in verified:raise AssertionError("UNEXPECTED_IDENTITY")
    source={"schema":"neumann.q3.source-derived-unbounded-integer-algebra-laws.v1",
       "prior_source_policy_sha256":digest,
       "source_fold_constructor":list(chosen),
       "semantic_hypotheses":results,
       "proved_properties":verified,
       "unproved_properties":[x["candidate_property"] for x in results if not x["proved"]],
       "source_only_boolean_theorem":prior.cross_type_law_check(prior.load_prior()["or_ast"]),
       "target_registry":TARGET,
       "human_written":"Candidate algebra property templates, integer datatype adapter, Z3 verifier, original corpus access."}
    source["sha256"]=prior.sha(source)
    pathlib.Path(METHOD).write_text(json.dumps(source,indent=2))
    print(json.dumps({"proved":verified,"refuted":source["unproved_properties"],
       "before_target_sha256":source["sha256"]},indent=2))
    return source

def original(name):
    # Deliberately allow only the separate predeclared second cohort.
    if name not in TARGET:raise ValueError("UNREGISTERED_TASK")
    with __import__("urllib.request").request.urlopen(prior.ROOT+name,timeout=25) as h:
        raw=h.read(250001)
    if len(raw)>250000:raise ValueError("OVERSIZE")
    return raw.decode()

def run_target():
    method=json.loads(pathlib.Path(METHOD).read_text())
    digest=method.pop("sha256")
    old,source_sha=prior_policy()
    if prior.sha(method)!=digest or method["prior_source_policy_sha256"]!=source_sha:
        raise ValueError("CHANGED_FROZEN_META_METHOD")
    chosen=tuple(method["source_fold_constructor"])
    print("ALGORITHMIC_METHOD_AND_MATH_CERTIFICATES_FROZEN",digest)
    rows=[];start=time.perf_counter()
    for category, names in COHORTS.items():
        for name in names:
            record={"cohort":category,"name":name}
            try:
                raw=original(name)
                task=prior.decode_original(raw)
                record.update({"original_sha256":hashlib.sha256(raw.encode()).hexdigest(),
                    "argument_count":len(task["params"])})
                record["memory"]=prior.prove_candidate(raw,chosen,timeout_ms=5000)
                baseline=[]
                for candidate in prior.all_variants():
                    verdict=prior.prove_candidate(raw,candidate,timeout_ms=5000)
                    baseline.append({"candidate":list(candidate),**verdict})
                    if verdict["status"]=="UNBOUNDED_INT_Z3_UNSAT":break
                record["cold"]={
                    "success":baseline[-1]["status"]=="UNBOUNDED_INT_Z3_UNSAT",
                    "num_proofs":len(baseline),
                    "proof_ms":round(sum(x["proof_ms"] for x in baseline),5),
                    "last_verdict":baseline[-1]["status"],
                    "attempts":baseline}
            except Exception as e:
                record["error"]=type(e).__name__+": "+str(e)[:190]
            rows.append(record)
    result={"schema":"neumann.q3.new-original-cross-family-algebraic-invariant-first.v1",
       "prior_integer_source_method_sha256":source_sha,
       "frozen_algebra_theorem_sha256":digest,
       "original_registry":COHORTS,
       "originals":len(TARGET),
       "summary":{category:{
           "count":sum(r["cohort"]==category for r in rows),
           "eligible":sum(r["cohort"]==category and "error" not in r for r in rows),
           "learned_unbounded_proved":sum(r["cohort"]==category and r.get("memory",{}).get("status")=="UNBOUNDED_INT_Z3_UNSAT" for r in rows),
           "cold_unbounded_proved":sum(r["cohort"]==category and r.get("cold",{}).get("success",False) for r in rows),
           "errors":sum(r["cohort"]==category and "error" in r for r in rows)}
           for category in COHORTS},
       "rows":rows,
       "total_run_s":round(time.perf_counter()-start,4),
       "scope":"This evaluates truly different integer subtypes, including negative OOD controls, but still one SyGuS benchmark provider. In-domain fold source max2/max3, human source/proof method. No global Q3/Q6 guarantee."}
    pathlib.Path(OUTPUT).write_text(json.dumps(result,indent=2))
    print(json.dumps(result["summary"],indent=2))
    return result

if __name__=="__main__":
    import sys
    if sys.argv[1:]==["source"]:source_law_discovery()
    elif sys.argv[1:]==["target"]:run_target()
    else:raise SystemExit("source|target")
