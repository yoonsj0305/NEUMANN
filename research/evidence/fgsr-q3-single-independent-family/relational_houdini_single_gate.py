"""Real original 48-clause RELATIONAL classical synthesis gate (opened development).

A single *fixed*, researcher-defined cross-thread predicate language:
 control/data implications, cross-thread phase exclusions, and safe PC exclusion.
Counterexample-guided inductive-conjunctive elimination (Houdini).

This is a non-neural baseline, not a NEUMANN Q3 claim, and a proof is required
over ALL 48 authentic ORIGINAL Horn clauses. No individual-result template edits.
"""
import hashlib,json,os,time,urllib.request
from pathlib import Path
import z3

REV="b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"
PATH="ultimate/LIA-NonLin/33_double_lock_p1_vs_simplified_000.smt2"
SHA="2dfd3f531151113401aca614ad3e4176dae77ebcb326abbbcc456551a9a8f645"
OUT=Path(os.getenv("FGSR_RESULT","relational_houdini_first.json"))
CHECK_TIMEOUT_MS=3500
MAX_ROUNDS=8
MAX_TOTAL_SMT_CHECKS=480
CONTROL_POS=(3,4,5,6,7)
DATA_POS=(0,1,2)
WORKER_VALUES=(-1,0,1,2,3,4,5,6,7,8)

def source_assertions(text):
    forms=z3.parse_smt2_string(text)
    if len(forms)!=48:raise ValueError("WRONG_NUMBER_ORIGINAL_ASSERTIONS:"+str(len(forms)))
    res=[]
    for ri,q in enumerate(forms,1):
        if not z3.is_quantifier(q) or not q.is_forall():raise ValueError("NON_FORALL_RULE:"+str(ri))
        fresh=[z3.Const(f"v_{ri}_{i}",q.var_sort(i)) for i in range(q.num_vars())]
        body=z3.substitute_vars(q.body(),*fresh)
        if body.decl().kind()!=z3.Z3_OP_IMPLIES:raise ValueError("NON_HORN_IMPLIES:"+str(ri))
        premise,head=body.children()
        atoms=[]
        def flatten(x):
            if z3.is_app(x) and x.decl().kind()==z3.Z3_OP_AND:
                for item in x.children():flatten(item)
            else:atoms.append(x)
        flatten(premise)
        calls=[a for a in atoms if z3.is_app(a) and a.decl().name()=="Inv"]
        guard=[a for a in atoms if a not in calls]
        if head.decl().name()=="Inv":kind="relation"
        elif head.decl().name()=="CHC_COMP_FALSE":kind="false_pred"
        elif z3.is_false(head):kind="false"
        else:raise ValueError("UNKNOWN_HEAD "+str(head))
        res.append({"index":ri,"body_calls":calls,"guard":guard,"head":head,"kind":kind})
    return res

def candidate_program():
    # An ordered static language, held fixed across checks; not learned output.
    # Function descriptions contain structure templates but NO goal-specific witnesses.
    templates=[]
    def append(name,tag,args):
        templates.append({"name":name,"tag":tag,"args":args})
    for p in CONTROL_POS:
        vals=(0,1,2,3,4) if p==7 else WORKER_VALUES
        append(f"range_pc{p}","range",(p,tuple(vals)))
    for p in CONTROL_POS:
        for v in WORKER_VALUES:
            append(f"pc{p}_neq_{v}","neq",(p,v))
    for p in CONTROL_POS:
        for v in WORKER_VALUES:
            for d in DATA_POS:
                for n in (-1,0,1):
                    append(f"pc{p}={v}_=>_x{d}={n}","cond_eq",(p,v,d,n))
    for p in (3,4,5,6):
        for q in range(p+1,7):
            for v in WORKER_VALUES:
                for w in WORKER_VALUES:
                    append(f"not(pc{p}={v}_pc{q}={w})","forbidden_pair",(p,v,q,w))
    # Intentionally registered bounded grammar; no posthoc expansions.
    return templates

def instantiate(t,arr):
    tag=t["tag"];x=t["args"]
    if tag=="range":
        pos,values=x
        return z3.Or(*[arr[pos]==z3.IntVal(v) for v in values])
    if tag=="neq":
        pos,value=x
        return arr[pos]!=z3.IntVal(value)
    if tag=="cond_eq":
        pos,val,d,n=x
        return z3.Implies(arr[pos]==z3.IntVal(val),arr[d]==z3.IntVal(n))
    if tag=="forbidden_pair":
        pos,v,q,w=x
        return z3.Or(arr[pos]!=z3.IntVal(v),arr[q]!=z3.IntVal(w))
    raise ValueError("UNKNOWN_TEMPLATE_TYPE")

def conj(tmpl,active,arr):
    if not active:return z3.BoolVal(True)
    return z3.And(*[instantiate(tmpl[i],arr) for i in sorted(active)])

def query(rule,templates,active,head_template=None):
    s=z3.Solver()
    s.set(timeout=CHECK_TIMEOUT_MS)
    body=[*rule["guard"]]
    body.extend(conj(templates,active,c.children()) for c in rule["body_calls"])
    s.add(*body)
    if rule["kind"]=="relation":
        atom=rule["head"]
        if head_template is not None:
            s.add(z3.Not(instantiate(templates[head_template],atom.children())))
        else:
            s.add(z3.Not(conj(templates,active,atom.children())))
    else:
        # CHC_COMP_FALSE interpreted FALSE to test the ORIGINAL safety query.
        pass
    start=time.perf_counter_ns()
    verdict=s.check()
    elapsed=round((time.perf_counter_ns()-start)/1e6,3)
    if verdict==z3.sat:
        m=s.model()
        falsified=[]
        if rule["kind"]=="relation":
            for i in sorted(active):
                if z3.is_false(m.eval(instantiate(templates[i],rule["head"].children()),model_completion=True)):
                    falsified.append(i)
        return "sat",falsified,elapsed
    if verdict==z3.unsat:return "unsat",[],elapsed
    return "unknown",[],elapsed

def main():
    start=time.perf_counter_ns()
    receipt={
        "experiment":"FGSR genuine original 48-clause cross-thread relational candidate induction",
        "source_sha256":SHA,"model_calls":0,"training":0,
        "candidate_kind":"RESEARCHER_FIXED_CROSS_THREAD_PREDICATE_LANGUAGE",
        "global_q":"OPEN","original_modified":False,
        "status":"BLOCKED",
        "rounds":[],"smt_checks":0,
        "z3_version":z3.get_version_string(),
        "limits":{"max_rounds":MAX_ROUNDS,"max_smt_checks":MAX_TOTAL_SMT_CHECKS,"per_check_ms":CHECK_TIMEOUT_MS}
    }
    try:
        url=f"https://raw.githubusercontent.com/chc-comp/chc-comp26-benchmarks/{REV}/{PATH}"
        with urllib.request.urlopen(url,timeout=30) as f:raw=f.read()
        if hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError("SOURCE_IDENTITY_FAILURE")
        rules=source_assertions(raw.decode())
        templates=candidate_program()
        active=set(range(len(templates)))
        receipt["frozen_language_size"]=len(templates)
        receipt["original_rules"]=len(rules)
        receipt["original_assertion_sha256_verified"]=True
        for step in range(MAX_ROUNDS):
            removed=set(); counterexamples=[]
            # Every rule is analyzed with one shared active set per round.
            for rule in rules:
                if rule["kind"]!="relation":continue
                if receipt["smt_checks"]>=MAX_TOTAL_SMT_CHECKS:raise RuntimeError("GLOBAL_SMT_CALL_CAP")
                verdict,false_at_head,ms=query(rule,templates,active)
                receipt["smt_checks"]+=1
                if verdict=="unknown":raise RuntimeError("SMT_UNKNOWN_OR_TIMEOUT_RULE_"+str(rule["index"]))
                if verdict=="sat":
                    if not false_at_head:raise RuntimeError("SAT_WITH_NO_INVALID_PREDICATE")
                    removed.update(false_at_head)
                    counterexamples.append({
                        "rule":rule["index"],"eliminated_at_this_model":len(false_at_head),"query_wall_ms":ms
                    })
            receipt["rounds"].append({
                "round":step+1,"active_before":len(active),"removed":len(removed),
                "counterexample_clauses":counterexamples[:12]
            })
            if not removed:break
            active.difference_update(removed)
        else:
            receipt["status"]="INCOMPLETE_ROUND_CAP"
        receipt["inductive_survivors"]=len(active)
        receipt["surviving_names"]=[templates[i]["name"] for i in sorted(active)]
        if receipt["status"]!="INCOMPLETE_ROUND_CAP":
            original=[]
            for rule in rules:
                if receipt["smt_checks"]>=MAX_TOTAL_SMT_CHECKS:raise RuntimeError("GLOBAL_SMT_CALL_CAP")
                ans,falsified,ms=query(rule,templates,active)
                receipt["smt_checks"]+=1
                original.append({"rule":rule["index"],"status":ans,"ms":ms})
            receipt["full_original_clause_verdicts"]=original
            receipt["all_original_unsat"]=all(item["status"]=="unsat" for item in original)
            receipt["original_unsat_count"]=sum(x["status"]=="unsat" for x in original)
            receipt["first_unproven_clause"]=next((x for x in original if x["status"]!="unsat"),None)
            receipt["status"]=(
                "ALL_48_ORIGINAL_HORN_CERTIFIED_FIXED_CLASSICAL_RELATION_LANGUAGE"
                if receipt["all_original_unsat"] else
                "GREATEST_FIXED_RELATIONAL_BASIS_INSUFFICIENT"
            )
    except Exception as exc:
        receipt["status"]="INCOMPLETE_BLOCKED"
        receipt["error"]=type(exc).__name__+": "+str(exc)[:850]
    receipt["total_wall_ms"]=round((time.perf_counter_ns()-start)/1e6,3)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    print("FGSR_RELATIONAL_HOUDINI",receipt["status"])
    print("SURVIVORS",receipt.get("inductive_survivors"))
    print("ORIGINAL_UNSAT",receipt.get("original_unsat_count"),"/48")
    print("CHECKS",receipt["smt_checks"])
    print("GLOBAL_Q",receipt["global_q"])

if __name__=="__main__":main()
