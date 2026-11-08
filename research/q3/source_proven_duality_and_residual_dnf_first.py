"""Q3 source-induced metarule generalization: proven Boolean duality + residual DNF.

SOURCE only: previously verified 16 bvsge original SC predicates and proof
that the source template uses OR. No target reference code, constraints, or
labels are fetched until frozen method file exists.
TARGET: untouched 32 official ic_bvugt and ic_ne inverse-condition originals.
Compared with same-language semantic classical rule generation.

The duality engine, DNF grammar, typed VM, search budgets and policy are
HUMAN WRITTEN. This experiment tests source-evidence conditioned method
activation, not independent self-invention of Boolean algebra.
"""
from __future__ import annotations
import hashlib,json,pathlib,time,itertools
import causal_invariant_boolean_existence_first as old

PREVIOUS="source_policy/Q3_BOOLEAN_INVARIANT_SOURCE_FROZEN.json"
METHOD="Q3_CAUSAL_DUAL_AND_DNF_SOURCE_FROZEN.json"
TARGET=[f"ic_{cmp}_{op}.sl" for cmp in ("bvugt","ne") for op in old.base.OPS]
assert len(TARGET)==32 and len(set(TARGET))==32
assert set(TARGET).isdisjoint(old.SOURCE+old.TARGET)

def verify_dual(op):
    dual={"or":"and","and":"or"}
    if op not in dual:raise ValueError("UNKNOWN_BOOLEAN_CONSTRUCTOR")
    # Exhaustive four-valued Boolean relation proof, not a hand-entered
    # table of outcomes for any benchmark task.
    for a,b in itertools.product((False,True),repeat=2):
        before=not ((not a) or (not b)) if op=="or" else not ((not a) and (not b))
        after=(a and b) if op=="or" else (a or b)
        if before!=after:raise ValueError("INVALID_OPERATOR_DUAL")
    return dual[op]

def atoms_with_negations(atoms):
    all_atoms=[]
    maskmap={}
    for p,mask in atoms:
        for val,node in ((mask,p),(old.FULL^mask,("not",p))):
            if val in maskmap:continue
            maskmap[val]=node
            all_atoms.append((node,val))
    return all_atoms

def dnf_from_residual(y,atoms,max_terms=3,pair_limit=150):
    """Generate two-level Boolean terms from sufficient-set invariants.

    Each candidate term T must satisfy T subseteq Y.
    Greedily cover Y with up to max_terms validated sufficient terms.
    Backtrack over a bounded first-term beam to escape local minima.
    No target family strings or solutions enter the algorithm.
    """
    if y==0:return ("const",False),0,{"terms":0}
    if y==old.FULL:return ("const",True),0,{"terms":0}
    candidates=atoms_with_negations(atoms)
    trials=0;implicants={}
    for p,mask in candidates:
        trials+=1
        if mask and mask&(~y)==0:
            implicants[mask]=p
    for i,(p,a) in enumerate(candidates):
        for q,b in candidates[i+1:]:
            trials+=1
            m=a&b
            if not m or m&(~y):continue
            node=("and",p,q)
            if m not in implicants or old.n_nodes(node)<old.n_nodes(implicants[m]):
                implicants[m]=node
    if not implicants:return None,trials,{"candidate_implicants":0}
    ordered=sorted(implicants.items(),key=lambda item:(
        -item[0].bit_count(),old.n_nodes(item[1]),old.canon(item[1])))
    # Limiting the first beam is only a compute budget; cannot manufacture
    # false positives, but can cause honest false-negative ABSTAIN.
    def greedy(rem,selected):
        for _ in range(max_terms-len(selected)):
            rank=sorted((( (mask&rem).bit_count(),-old.n_nodes(p),mask,p)
                         for mask,p in ordered),reverse=True)
            if not rank or rank[0][0]==0:return None
            _,_,mask,p=rank[0]
            selected=selected+[(p,mask)]
            rem=rem&(~mask)
            if not rem:return selected
        return None
    options=[]
    top=ordered[:pair_limit]
    for p,mask in [(None,0)]+[(node,m) for m,node in top]:
        prefix=[] if p is None else [(p,mask)]
        remaining=y if p is None else y&(~mask)
        result=prefix if not remaining else greedy(remaining,prefix)
        trials+=1
        if result:
            ast=result[0][0]
            for node,_ in result[1:]:
                ast=("or",ast,node)
            if old.independently_check(ast,y):
                options.append((old.n_nodes(ast),old.canon(ast),ast,len(result)))
    if options:
        cost,_,ast,num=min(options)
        return ast,trials,{"terms":num,"source_sufficient_components":len(implicants)}
    return None,trials,{"candidate_implicants":len(implicants)}

def source_only():
    prev=json.loads(pathlib.Path(PREVIOUS).read_text())
    proof=prev.pop("sha256")
    if old.sha(prev)!=proof or prev["source_registry"]!=old.SOURCE:
        raise ValueError("SOURCE_FIRST_PROVENANCE_ERROR")
    allowed=prev["enabled_compositions"]
    if not allowed:raise ValueError("EMPTY_SOURCE_RULES")
    derived={x:verify_dual(x) for x in allowed}
    comps=list(dict.fromkeys(allowed+list(derived.values())))
    atoms=old.atom_library()
    records=[]
    for name in old.SOURCE:
        rec={"id":name}
        try:
            original=old.fetch(name)
            y,_=old.existential_truth(original)
            fixed,_,_=old.invariant_solve(y,atoms,prev)
            dnf,checks,cert=dnf_from_residual(y,atoms)
            rec.update({"previous_proved":old.independently_check(fixed,y),
               "dnf_proved":old.independently_check(dnf,y),
               "dnf_only_new_solve":dnf is not None and fixed is None,
               "dnf_ast":dnf,"predicate_trials":checks,"certificate":cert})
        except Exception as e:rec["error"]=type(e).__name__+": "+str(e)[:170]
        records.append(rec)
    extension=sum(int(x.get("dnf_only_new_solve",False)) for x in records)
    model={"schema":"neumann.q3.causal-method-closure-from-source.v1",
      "source_first_run":42434312622,
      "source_original_sha256":proof,
      "source_proven_boolean_constructors":allowed,
      "exhaustively_verified_dual_constructors":derived,
      "new_available_operations":comps,
      "dnf_source_new_exact_tasks":extension,
      "dnf_enabled_by_source_counterexample":extension>0,
      "dnf_max_terms":3,
      "source_causal_records":records,
      "human_supplied":"DeMorgan duality verifier, sufficient-set DNF grammar, exact finite-domain evaluator, search budgets"}
    model["sha256"]=old.sha(model)
    pathlib.Path(METHOD).write_text(json.dumps(model,indent=2))
    print(json.dumps({"source_dual_generated":derived,"source_dnf_new":extension,
        "dnf_enabled":model["dnf_enabled_by_source_counterexample"],
        "source_errors":sum("error" in x for x in records),
        "method_sha256":model["sha256"]},indent=2))
    return model

def target_only():
    model=json.loads(pathlib.Path(METHOD).read_text())
    check=model.pop("sha256")
    if old.sha(model)!=check or model["source_first_run"]!=42434312622:
        raise ValueError("MODIFIED_AFTER_FROZEN_SOURCE")
    print("TARGET_NOT_ACCESSED_BEFORE_SHA",check)
    atoms=old.atom_library()
    records=[];start=time.perf_counter()
    for name in TARGET:
        rec={"id":name}
        try:
            raw=old.fetch(name)
            y,_=old.existential_truth(raw)
            rec["original_sha256"]=hashlib.sha256(raw.encode()).hexdigest()
            rec["semantic_role"]=old.semantic_role(y)
            rec["positive_pair_count"]=y.bit_count()
            arms={}
            for label,enabled,use_dnf in (
                ("prior_source_or",model["source_proven_boolean_constructors"],False),
                ("autogenerated_dual",model["new_available_operations"],False),
                ("source_guided_residual",model["new_available_operations"],model["dnf_enabled_by_source_counterexample"]),
                ("strong_semantic_classical",["and","or"],True)):
                st=time.perf_counter_ns()
                p,c,certificate=old.invariant_solve(y,atoms,{"enabled_compositions":enabled})
                checks=c
                if p is None and use_dnf:
                    p,additional,extra=dnf_from_residual(y,atoms)
                    checks+=additional
                    certificate={"new_dnf":extra}
                arm={"exact_256":old.independently_check(p,y),
                     "checks":checks,
                     "search_ms":round((time.perf_counter_ns()-st)/1e6,5),
                     "program_ast":p,
                     "certificate":certificate}
                arms[label]=arm
                if p is not None and not arm["exact_256"]:
                    raise ValueError("BUG_PROGRAM_NOT_EQUIVALENT")
            rec["arms"]=arms
        except Exception as e:rec["error"]=type(e).__name__+": "+str(e)[:170]
        records.append(rec)
    arms=("prior_source_or","autogenerated_dual","source_guided_residual",
          "strong_semantic_classical")
    results={key:{"exact_originals":sum(int(r.get("arms",{}).get(key,{}).get("exact_256",False)) for r in records),
                  "candidate_checks":sum(r.get("arms",{}).get(key,{}).get("checks",0) for r in records),
                  "search_ms":round(sum(r.get("arms",{}).get(key,{}).get("search_ms",0) for r in records),5)}
             for key in arms}
    result={"schema":"neumann.q3.source-duality-residual-first-32-formal-boolean.v1",
      "source_method_sha256":check,
      "target_registry":TARGET,"source_only_development_originals":old.SOURCE,
      "full_input_pairs":256,
      "summary":results,"errors":sum("error" in x for x in records),
      "records":records,"total_target_elapsed_s":round(time.perf_counter()-start,4),
      "limits":"Source-adaptive activation, human-authored De Morgan schema and DNF model; classical receives exact same grammar. Separate solved-task lift from search-time lift."}
    pathlib.Path("Q3_CAUSAL_DUAL_FRESH_ORIGINAL_FIRST.json").write_text(json.dumps(result,indent=2))
    print(json.dumps({"fresh_originals":len(TARGET),"errors":result["errors"],
                      "results":results,"source_model":check},indent=2))
    return result

if __name__=="__main__":
    import sys
    if sys.argv[1:]==["source"]:source_only()
    elif sys.argv[1:]==["target"]:target_only()
    else:raise SystemExit("source|target")
