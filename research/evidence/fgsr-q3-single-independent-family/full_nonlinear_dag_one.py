"""FGSR full nonlinear Horn proof-DAG bounded checker on a pinned ORIGINAL source.

Scientific roles: strongest-classical development diagnostic and future learned
proposer verifier. NOT a learned model, NOT an exhaustive safety solver.

Unlike the prior linear-only trace, every original positive rule including
nonlinear AND-premises participates. A SAT result is *independently replayed*
step-by-step using untouched original Horn clauses, including terminal false.
No path: INCOMPLETE, never a safety proof. No original source rewriting.
"""
import hashlib,json,os,time,urllib.request
from pathlib import Path
import z3

ROOT="https://raw.githubusercontent.com/chc-comp/chc-comp26-benchmarks/"
REV="b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"
SRC="ultimate/LIA-NonLin/33_double_lock_p1_vs_simplified_000.smt2"
SHA="2dfd3f531151113401aca614ad3e4176dae77ebcb326abbbcc456551a9a8f645"
OUT=Path(os.environ.get("FGSR_RESULT","nonlinear_dag_receipt.json"))
BUDGET=[(6,12000),(10,16000),(14,25000),(18,35000)]
WALL_CAP_SECONDS=112

def read_rules(data,expected_count=48):
    formulas=z3.parse_smt2_string(data)
    if len(formulas)!=expected_count:raise ValueError("ORIGINAL_CLAUSE_COUNT_MISMATCH")
    rules=[]
    for i,f in enumerate(formulas,1):
        if not (z3.is_quantifier(f) and f.is_forall()):raise ValueError("NOT_FORALL_"+str(i))
        fresh=[z3.Const(f"original_{i}_local_{j}",f.var_sort(j)) for j in range(f.num_vars())]
        body=z3.substitute_vars(f.body(),*fresh)
        if not z3.is_implies(body):raise ValueError("NOT_HORN_"+str(i))
        prem,head=body.children()
        atoms=[]
        def flatten(node):
            if z3.is_and(node):
                for arg in node.children():flatten(arg)
            else:atoms.append(node)
        flatten(prem)
        calls=[x for x in atoms if z3.is_app(x) and x.decl().name()=="Inv"]
        guards=[x for x in atoms if not (z3.is_app(x) and x.decl().name()=="Inv")]
        kind=head.decl().name()
        if kind not in ("Inv","CHC_COMP_FALSE","false"):
            if not z3.is_false(head):raise ValueError("UNKNOWN_HEAD_"+str(i))
            kind="false"
        rules.append({"id":i,"vars":fresh,"body":calls,"guards":guards,"head":head,"kind":kind})
    if expected_count==48:
        if sum(x["kind"]=="Inv" for x in rules)!=45:raise ValueError("INV_HEAD_COUNT_UNEXPECTED")
        if sum(x["kind"]=="CHC_COMP_FALSE" for x in rules)!=2:raise ValueError("GOAL_COUNT_UNEXPECTED")
        if sum(x["kind"]=="false" for x in rules)!=1:raise ValueError("TERMINAL_COUNT_UNEXPECTED")
    return rules

def inst(rule,prefix):
    replace=[(old,z3.Const(f"{prefix}_{j}",old.sort())) for j,old in enumerate(rule["vars"])]
    def s(x):return z3.substitute(x,*replace) if replace else x
    return {
        "id":rule["id"],"kind":rule["kind"],
        "guards":[s(x) for x in rule["guards"]],
        "body":[s(x) for x in rule["body"]],
        "head":s(rule["head"])
    }

def check_replay(rules,proof):
    checked=[]
    for ix,node in enumerate(proof["nodes"]):
        rule=rules[node["rule"]-1]
        if rule["kind"]!="Inv":raise ValueError("REPLAY_WRONG_HEAD")
        if len(rule["body"])!=len(node["parents"]):raise ValueError("REPLAY_WRONG_PARENT_COUNT")
        if any(p>=ix or p<0 for p in node["parents"]):raise ValueError("REPLAY_TOPOLOGICAL_FAILURE")
        rr=inst(rule,f"independent_replay_{ix}")
        solver=z3.Solver();solver.set(timeout=1500)
        solver.add(*rr["guards"])
        solver.add(*[rr["head"].arg(j)==node["state"][j] for j in range(8)])
        for p,call in zip(node["parents"],rr["body"]):
            solver.add(*[call.arg(j)==proof["nodes"][p]["state"][j] for j in range(8)])
        result=str(solver.check())
        checked.append({"node":ix,"rule":rule["id"],"result":result})
        if result!="sat":raise ValueError("REPLAY_STEP_"+str(ix)+"_"+result)
    terminal=proof["nodes"][-1]["state"]
    goals=[]
    for rule in rules:
        if rule["kind"]!="CHC_COMP_FALSE":continue
        if len(rule["body"])!=1:raise ValueError("REPLAY_UNEXPECTED_ERROR_ARITY")
        rr=inst(rule,f"independent_error_{rule['id']}")
        s=z3.Solver();s.set(timeout=1500);s.add(*rr["guards"])
        s.add(*[rr["body"][0].arg(j)==terminal[j] for j in range(8)])
        if s.check()==z3.sat:goals.append(rule["id"])
    false_rules=[rule for rule in rules if rule["kind"]=="false"]
    if len(false_rules)!=1 or not any(z3.is_app(x) and x.decl().name()=="CHC_COMP_FALSE" for x in false_rules[0]["guards"]):
        raise ValueError("REPLAY_NO_TERMINAL_REFUTATION_RULE")
    if not goals:raise ValueError("REPLAY_NO_ORIGINAL_ERROR_RULE")
    return {"independently_replayed":True,"checked_nodes":len(checked),
            "step_checks":checked,"triggered_original_goals":goals,
            "terminal_false_rule":false_rules[0]["id"]}

def attempt(rules,nodes,cap_ms):
    t0=time.monotonic()
    rule_choices=[r for r in rules if r["kind"]=="Inv"]
    states=[[z3.Int(f"node_{i}_v{j}") for j in range(8)] for i in range(nodes)]
    choice=[z3.Int(f"choice_{i}") for i in range(nodes)]
    parent=[[z3.Int(f"parent_{i}_{k}") for k in range(3)] for i in range(nodes)]
    solver=z3.Solver()
    solver.set(timeout=cap_ms)
    initial=[r for r in rule_choices if not r["body"]]
    if len(initial)!=1:raise ValueError("INIT_ARITY_DIFFERENT")
    # Root must follow the original initialization rule with arbitrary data.
    root=inst(initial[0],"root")
    solver.add(*root["guards"])
    solver.add(choice[0]==initial[0]["id"])
    solver.add(*[states[0][j]==root["head"].arg(j) for j in range(8)])
    for i in range(1,nodes):
        alternatives=[]
        def symbolic_state(ref):
            # For every variable index j, pick a topologically earlier fact.
            return [states[0][j] for j in range(8)] if i==1 else [
                __import__("functools").reduce(
                    lambda expr, ix:z3.If(ref==ix,states[ix][j],expr),
                    range(1,i),states[0][j])
                for j in range(8)]
        derefs=[symbolic_state(parent[i][k]) for k in range(3)]
        for rule in rule_choices:
            arity=len(rule["body"])
            if arity>3:raise ValueError("RULE_TOO_MANY_PREMISES")
            rr=inst(rule,f"step_{i}_rule_{rule['id']}")
            parts=[choice[i]==rule["id"],*rr["guards"]]
            parts.extend(states[i][j]==rr["head"].arg(j) for j in range(8))
            for k,atom in enumerate(rr["body"]):
                parts.append(parent[i][k]>=0)
                parts.append(parent[i][k]<i)
                parts.extend(atom.arg(j)==derefs[k][j] for j in range(8))
            alternatives.append(z3.And(*parts))
        solver.add(z3.Or(*alternatives))
    error_rules=[r for r in rules if r["kind"]=="CHC_COMP_FALSE"]
    actual_error_disjuncts=[]
    for err in error_rules:
        ee=inst(err,f"goal_{nodes}_original_rule_{err['id']}")
        if len(ee["body"])!=1:raise ValueError("UNSUPPORTED_ERROR_RULE_PREMISES")
        atom=ee["body"][0]
        actual_error_disjuncts.append(z3.And(
            *ee["guards"],
            *[atom.arg(j)==states[-1][j] for j in range(8)]
        ))
    if not actual_error_disjuncts:raise ValueError("NO_ORIGINAL_UNSAFETY_GOAL")
    solver.add(z3.Or(*actual_error_disjuncts))
    start=time.monotonic()
    result=solver.check()
    if result!=z3.sat:
        return {"nodes":nodes,"verdict":str(result),
                "build_ms":round((start-t0)*1000,3),
                "solve_ms":round((time.monotonic()-start)*1000,3)}
    model=solver.model()
    history=[]
    rules_by_id={r["id"]:r for r in rule_choices}
    for i in range(nodes):
        rid=model.eval(choice[i],model_completion=True).as_long()
        rule=rules_by_id[rid]
        history.append({
            "rule":rid,"parents":[model.eval(parent[i][k],model_completion=True).as_long()
                                    for k in range(len(rule["body"]))],
            "state":[model.eval(states[i][j],model_completion=True).as_long() for j in range(8)]
        })
    proof={"nodes":history}
    proof["certificate"]=check_replay(rules,proof)
    return {"nodes":nodes,"verdict":"sat","certificate":proof,
            "build_ms":round((start-t0)*1000,3),
            "solve_ms":round((time.monotonic()-start)*1000,3)}

def main():
    t0=time.monotonic()
    result={"study":"FGSR full nonlinear ORIGINAL exact finite Horn derivation DAG",
            "source_sha256":SHA,"source_modified":False,"model_calls":0,
            "neumann_learned":False,"q1_q7":"OPEN","status":"NOT_RUN",
            "node_budgets":BUDGET,"single_original":True,"case_opened_development":True,
            "z3_version":z3.get_version_string(),"attempts":[]}
    try:
        url=ROOT+REV+"/"+SRC
        with urllib.request.urlopen(url,timeout=25) as f:raw=f.read()
        if hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError("ORIGINAL_SHA_MISMATCH")
        rules=read_rules(raw.decode())
        result["premise_arities"]={str(k):sum(len(r["body"])==k for r in rules)
                                   for k in range(4)}
        result["nonlinear_original_rules_included"]=sum(len(r["body"])>=2 for r in rules)
        for n,cap in BUDGET:
            if time.monotonic()-t0>WALL_CAP_SECONDS:
                result["status"]="INCOMPLETE_GLOBAL_TIME_CAP";break
            attempt_result=attempt(rules,n,cap)
            result["attempts"].append(attempt_result)
            if attempt_result["verdict"]=="sat":
                result["status"]="ORIGINAL_UNSAT_CERTIFIED_FINITE_HORN_DAG";break
        else:
            result["status"]="NO_FINITE_WITNESS_IN_BUDGET_NOT_SAFETY_PROOF"
    except Exception as exc:
        result["status"]="BLOCKED_OR_ENGINEERING_ERROR"
        result["error"]=type(exc).__name__+": "+str(exc)[:900]
    result["elapsed_ms"]=round((time.monotonic()-t0)*1000,3)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("ORIGINAL_NONLINEAR_DAG",result["status"])
    print("SOLVES",[(a["nodes"],a["verdict"]) for a in result["attempts"]])
    print("ALL_Q",result["q1_q7"])

if __name__=="__main__":main()
