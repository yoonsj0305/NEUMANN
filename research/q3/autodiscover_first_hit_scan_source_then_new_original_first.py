"""NEUMANN Q3 | autonomously select new CONSTRUCTOR CONTROL GRAPH on SOURCE failure.

A previous source-proven max-fold method is frozen but FAILS an integer
array-sum priority problem. A human-defined generic constructor search
space includes a NEW "first-hit sequential scan" control structure.

Source originals: jmbl_fg_array_sum_2_5 and _3_5, previously used as
OUT-OF-DOMAIN developer controls, now deliberately EXPOSED SOURCE only.
The chosen executable method is frozen BEFORE target byte access.

New original targets: 13 untouched SyGuS CLIA array_sum problems:
6 higher input counts with threshold 5 and 7 with unseen threshold 15.
The target numeric threshold is read as a symbolic constant from the
OFFICIAL PROBLEM SPECIFICATION, not from task ID/reference solution.

The generic method inventor, grammar, SMT executor and threshold extraction
are all HUMAN CODED. This is bounded autonomous constructor selection and
cross-threshold transfer, NOT a universal autonomous meta-algorithm.
"""
from __future__ import annotations
import hashlib,json,pathlib,re,time,urllib.request
import z3
import cross_theory_boolean_invariant_to_unbounded_lia_first as old

SOURCE=[
 "jmbl_fg_array_sum_2_5.sl",
 "jmbl_fg_array_sum_3_5.sl"]
TARGET=[
 "jmbl_fg_array_sum_4_5.sl","jmbl_fg_array_sum_6_5.sl",
 "jmbl_fg_array_sum_7_5.sl","jmbl_fg_array_sum_8_5.sl",
 "jmbl_fg_array_sum_9_5.sl","jmbl_fg_array_sum_10_5.sl",
 "jmbl_fg_array_sum_4_15.sl","jmbl_fg_array_sum_5_15.sl",
 "jmbl_fg_array_sum_6_15.sl","jmbl_fg_array_sum_7_15.sl",
 "jmbl_fg_array_sum_8_15.sl","jmbl_fg_array_sum_9_15.sl",
 "jmbl_fg_array_sum_10_15.sl"]
assert len(TARGET)==13 and len(set(TARGET))==13
assert set(SOURCE).isdisjoint(TARGET+old.SOURCE+old.TARGET)
PRIOR="prior/Q3_CROSS_THEORY_INTEGER_SOURCE_POLICY_FROZEN.json"
BOOL="frozen_bool/Q3_AUTO_DISCOVERED_BOOLEAN_METHOD_LAWS_SOURCE.json"
MODEL="Q3_NEW_SCAN_CONSTRUCTOR_SOURCE_FROZEN.json"
OUTPUT="Q3_SOURCE_DISPATCH_SCAN_13_INTEGER_ORIGINAL_FIRST.json"
PAIR_OPS=("-","+")
GUARDS=(">","<=",">=","<")
DIRECTIONS=("forward","reverse")

def canonical(o):return json.dumps(o,sort_keys=True,separators=(",",":"))
def sha(o):return hashlib.sha256(canonical(o).encode()).hexdigest()

def load_prior():
    p=json.loads(pathlib.Path(PRIOR).read_text())
    proof=p.pop("sha256")
    if old.sha(p)!=proof or p["integer_source_names"]!=old.SOURCE:
        raise ValueError("OLD_METHOD_PROVENANCE_INVALID")
    b=json.loads(pathlib.Path(BOOL).read_text())
    check=b.pop("sha256")
    if old.sha(b)!=check or b["source_original_run"]!=42434312622:
        raise ValueError("BOOL_METHOD_PROVENANCE_INVALID")
    previous=p["frozen_boolean_source"]
    if previous["frozen_source_sha256"]!=check:raise ValueError("CROSS_TYPE_CHAIN_BROKEN")
    if not any(x["truth_signature"]==14 for x in b["functions"]):
        raise ValueError("NO_VALID_BOOLEAN_OR")
    return p,proof,check

def fetch(name):
    if name not in SOURCE+TARGET:raise ValueError("UNREGISTERED_NAME")
    with urllib.request.urlopen(old.ROOT+name,timeout=25) as r:
        data=r.read(200001)
    if len(data)>200000:raise ValueError("FILE_TOO_BIG")
    return data.decode()

def constants(task):
    # The threshold is only a grammar parameter sourced from constraint
    # numerals. No candidate-specific answer is read from task name.
    symbols=[]
    def recurse(node):
        if isinstance(node,list):
            for x in node:recurse(x)
        elif isinstance(node,str) and re.fullmatch(r"-?\d+",node):
            symbols.append(int(node))
    for expr in task["constraints"]:recurse(expr)
    return sorted({x for x in symbols if x>0 and x<=1000})

def scan_body(params,candidate,k):
    """The first matching adjacent-pair expression is returned. Pair op,
    condition and scan orientation are source-discovered program parameters.
    """
    op,cmp,direction=candidate
    terms=[]
    for l,r in zip(params,params[1:]):
        pair=f"({op} {l} {r})"
        terms.append((f"({cmp} {pair} {k})",pair))
    if direction=="forward":
        ordered=terms
    elif direction=="reverse":
        ordered=terms[::-1]
    else:raise ValueError("UNKNOWN_DIRECTION")
    out="0"
    for guard,val in reversed(ordered):
        out=f"(ite {guard} {val} {out})"
    return out

def compile_original(raw,body):
    task=old.decode_original(raw)
    f=task["name"];params=task["params"]
    lines=["(set-logic LIA)",
      f"(define-fun {f} ("+" ".join(f"({p} Int)" for p in params)+f") Int {body})"]
    constraints=[]
    for row in task["forms"]:
        if not row:continue
        tag=row[0]
        if tag in ("set-logic","synth-fun","check-synth"):continue
        if tag=="declare-var":
            if len(row)!=3 or row[2]!="Int":raise ValueError("BAD_VARIABLE")
            lines.append(f"(declare-const {row[1]} Int)")
        elif tag=="define-fun":lines.append(old.serialize(row))
        elif tag=="constraint":
            if len(row)!=2:raise ValueError("BAD_CONSTRAINT")
            constraints.append(old.serialize(row[1]))
        else:raise ValueError("UNKNOWN_CONTRACT_"+tag)
    if len(constraints)!=len(task["constraints"]):raise ValueError("MISSING_CONSTRAINT")
    lines.append("(assert (not (and "+" ".join(constraints)+")))")
    return "\n".join(lines)

def prove(raw,candidate,k,timeout_ms=5000):
    t=time.perf_counter_ns()
    task=old.decode_original(raw)
    body=scan_body(task["params"],candidate,k)
    formula=compile_original(raw,body)
    solver=z3.Solver();solver.set("timeout",timeout_ms)
    solver.from_string(formula)
    ans=solver.check()
    if ans==z3.unsat:verdict="PROVED_ALL_INTEGERS"
    elif ans==z3.sat:verdict="SAT_COUNTEREXAMPLE"
    else:verdict="UNKNOWN_TIMEOUT"
    return {"status":verdict,"elapsed_ms":round((time.perf_counter_ns()-t)/1e6,5),
            "program_body":body,
            "counterexample":str(solver.model())[:400] if ans==z3.sat else None}

def variants():
    return [(a,b,c) for a in PAIR_OPS for b in GUARDS for c in DIRECTIONS]

def source_only():
    previous,fold_hash,bool_hash=load_prior()
    raw=fetch(SOURCE[0]);raw2=fetch(SOURCE[1])
    old_fold=tuple(previous["learned_fold_constructor"])
    old_s=old.prove_candidate(raw,old_fold)
    if old_s["status"]=="UNBOUNDED_INT_Z3_UNSAT":
        raise AssertionError("OLD_METHOD_UNEXPECTEDLY_VALID")
    source_task=old.decode_original(raw)
    source_ks=constants(source_task)
    if not source_ks:raise ValueError("SOURCE_NO_DECLARED_CONSTANT")
    candidates=[];eligible=[]
    for k in source_ks:
        for program in variants():
            result=prove(raw,program,k)
            record={"program":list(program),"parameter":k,
                    "status":result["status"],"elapsed_ms":result["elapsed_ms"]}
            candidates.append(record)
            if result["status"]=="PROVED_ALL_INTEGERS":
                eligible.append((program,k))
    if not eligible:raise ValueError("NO_PROVABLE_NEW_CONSTRUCTOR")
    trial=[]
    for program,k in eligible:
        ret=prove(raw2,program,k)
        trial.append({"program":list(program),"parameter":k,
                      "status":ret["status"],"elapsed_ms":ret["elapsed_ms"]})
    proven=[x for x in trial if x["status"]=="PROVED_ALL_INTEGERS"]
    if not proven:raise ValueError("NO_SOURCE_INPUT_COUNT_GENERALIZATION")
    # Source-only deterministic model selection: first two-source proven
    # program, then replace hardcoded threshold with a typed constraint hole.
    chosen=tuple(proven[0]["program"])
    result={"schema":"neumann.q3.new-source-certified-first-hit-scan-meta-constructor.v1",
      "prior_bitvector_source_sha256":bool_hash,
      "prior_integer_fold_sha256":fold_hash,
      "source_originals":SOURCE,
      "source_checksums":[hashlib.sha256(raw.encode()).hexdigest(),
                          hashlib.sha256(raw2.encode()).hexdigest()],
      "old_fold_source_status":old_s["status"],
      "candidate_control_graphs":len(variants())*len(source_ks),
      "source_all_candidates":candidates,
      "source_two_n_certified":trial,
      "new_constructor_kind":"FIRST_HIT_ADJACENT_PAIR_SCAN",
      "new_constructor_parameters":list(chosen),
      "threshold_binding":"positive numeric constants present in target formal constraints, not task filename",
      "source_mutation":"FOLD failed, scan chosen from independently proven candidate source grammar",
      "new_target_registry":TARGET,
      "human_code":"Constructor graph templates, candidate symbols, constraint parser, Z3 test harness, typed threshold extraction"}
    result["sha256"]=sha(result)
    pathlib.Path(MODEL).write_text(json.dumps(result,indent=2))
    print(json.dumps({"old_method_source_status":old_s["status"],
        "source_graphs_tested":result["candidate_control_graphs"],
        "new_method":result["new_constructor_parameters"],
        "two_source_certified":len(proven),
        "frozen_source_sha256":result["sha256"]},indent=2))
    return result

def target_first():
    prev,old_hash,bool_hash=load_prior()
    model=json.loads(pathlib.Path(MODEL).read_text())
    signature=model.pop("sha256")
    if sha(model)!=signature or model["prior_integer_fold_sha256"]!=old_hash:
        raise ValueError("SOURCE_META_PROGRAM_CHANGED")
    if model["prior_bitvector_source_sha256"]!=bool_hash:
        raise ValueError("BOOL_META_PROGRAM_CHANGED")
    if model["new_target_registry"]!=TARGET:
        raise ValueError("TARGET_REGISTRY_CHANGED")
    print("SOURCE_INVENTED_CONTROL_GRAPH_FROZEN_BEFORE_NEW_TARGET",signature)
    rows=[];time0=time.perf_counter()
    learned=tuple(model["new_constructor_parameters"])
    for name in TARGET:
        record={"id":name}
        try:
            raw=fetch(name)
            task=old.decode_original(raw)
            parameters=constants(task)
            record["original_sha256"]=hashlib.sha256(raw.encode()).hexdigest()
            record["arity"]=len(task["params"])
            record["constraint_numeric_bindings"]=parameters
            if not parameters:raise ValueError("NO_NUMERIC_THRESHOLD_SYMBOL")
            # Learned: same generated template, threshold is bound from
            # target FORMAL specification, not from target filename.
            learned_trials=[{"k":k,**prove(raw,learned,k)} for k in parameters]
            submitted=next((x for x in learned_trials
                            if x["status"]=="PROVED_ALL_INTEGERS"),None)
            record["learned"]={
                 "proof":submitted is not None,
                 "queries":len(learned_trials),
                 "elapsed_ms":round(sum(x["elapsed_ms"] for x in learned_trials),5),
                 "trials":learned_trials}
            cold=[];found=None
            for k in parameters:
                for variant in variants():
                    pr=prove(raw,variant,k)
                    cold.append({"candidate":list(variant),"k":k,**pr})
                    if pr["status"]=="PROVED_ALL_INTEGERS":
                        found=(variant,k);break
                if found:break
            record["same_grammar_classical"]={
                "proof":found is not None,"queries":len(cold),
                "elapsed_ms":round(sum(x["elapsed_ms"] for x in cold),5),
                "trials":cold}
        except Exception as e:
            record["error"]=type(e).__name__+": "+str(e)[:200]
        rows.append(record)
    summary={"originals":len(TARGET),
        "errors":sum("error" in x for x in rows),
        "learned_unbounded_proved":sum(x.get("learned",{}).get("proof",False) for x in rows),
        "cold_unbounded_proved":sum(x.get("same_grammar_classical",{}).get("proof",False) for x in rows),
        "learned_proof_queries":sum(x.get("learned",{}).get("queries",0) for x in rows),
        "cold_proof_queries":sum(x.get("same_grammar_classical",{}).get("queries",0) for x in rows),
        "learned_proof_ms":round(sum(x.get("learned",{}).get("elapsed_ms",0) for x in rows),5),
        "cold_proof_ms":round(sum(x.get("same_grammar_classical",{}).get("elapsed_ms",0) for x in rows),5),
        "changed_threshold_originals":sum("15" in x["id"] and x.get("learned",{}).get("proof",False) for x in rows)}
    out={"schema":"neumann.q3.new-control-program-13-original-lia-first.v1",
      "source_sha256":signature,
      "source_original_run":42436072641,
      "upstream_commit":old.UPSTREAM,
      "new_target_registry":TARGET,
      "full_verification_domain":"UNBOUNDED_LIA_SMT_Z3",
      "summary":summary,"rows":rows,
      "target_wall_s":round(time.perf_counter()-time0,4),
      "limitations":"Targets are a single related array-sum family from same benchmark publisher; two source tasks were inspected as development before freezing target. The 16 candidate scan templates and threshold extraction are human-coded. This demonstrates bounded method selection and threshold/arity transfer, NOT global Q3 autonomy."}
    pathlib.Path(OUTPUT).write_text(json.dumps(out,indent=2))
    print(json.dumps(summary,indent=2))
    return out

if __name__=="__main__":
    import sys
    if sys.argv[1:]==["source"]:source_only()
    elif sys.argv[1:]==["target"]:target_first()
    else:raise SystemExit("source|target")
