"""FGSR decisive original-error reachability attempt, ORIGINAL 48 Horn rules.

Proof objective is *concrete* finite counterexample derivation, not conjecture:
base Inv facts => original single-Inv rules => original CHC_COMP_FALSE
=> original false. If SAT: replay every transition and both error clauses
against the original parsed Horn formulas; save exact states and rule indices.

This under-approximates the original nonlinear Horn semantics: multi-premise
rules are NOT used. UNSAT at a bounded depth proves NOTHING about safety.
No neural calls. No model Q promotion. No script generated target theorem.
"""
import hashlib,json,os,time,urllib.request
from pathlib import Path
import z3

REV="b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"
ORIGINAL="ultimate/LIA-NonLin/33_double_lock_p1_vs_simplified_000.smt2"
SOURCE_SHA="2dfd3f531151113401aca614ad3e4176dae77ebcb326abbbcc456551a9a8f645"
MAX_DEPTH=34
CAP_MS=85000
OUT=Path(os.environ.get("FGSR_RESULT","reachability_receipt.json"))

def original_clauses(data):
    forms=z3.parse_smt2_string(data)
    if len(forms)!=48:raise ValueError("EXPECTED_EXACTLY_48_ORIGINAL_CLAUSES")
    clauses=[]
    for idx,q in enumerate(forms,1):
        if not (z3.is_quantifier(q) and q.is_forall()):raise ValueError("UNSUPPORTED_ORIGINAL_QUANTIFIER")
        locals_=[z3.Const(f"native_{idx}_{i}",q.var_sort(i)) for i in range(q.num_vars())]
        phi=z3.substitute_vars(q.body(),*locals_)
        if not z3.is_implies(phi):raise ValueError("UNSUPPORTED_NON_IMPLICATION")
        premise,head=phi.children()
        calls=[]
        guard=[]
        def visit(x):
            if z3.is_and(x):
                for v in x.children():visit(v)
            elif z3.is_app(x) and x.decl().name()=="Inv":calls.append(x)
            else:guard.append(x)
        visit(premise)
        head_name=head.decl().name()
        clauses.append({"id":idx,"locals":locals_,"source":q,
                        "premise":premise,"head":head,
                        "calls":calls,"guard":guard,"head_name":head_name})
    return clauses

def fresh(clauses,idx,k):
    c=clauses[idx]
    old=c["locals"]
    new=[z3.Const(f"step_{k}_r{c['id']}_{j}",v.sort()) for j,v in enumerate(old)]
    pairs=list(zip(old,new))
    def replace(x):return z3.substitute(x,*pairs) if pairs else x
    return {"id":c["id"],"head":replace(c["head"]),
            "calls":[replace(a) for a in c["calls"]],
            "guard":[replace(a) for a in c["guard"]]}

def edge(prev,nxt,rule):
    return z3.And(*rule["guard"],
        *[prev[j]==rule["calls"][0].arg(j) for j in range(8)],
        *[nxt[j]==rule["head"].arg(j) for j in range(8)])

def triple_to_list(vec,model):
    return [model.eval(e,model_completion=True).as_long() for e in vec]

def recheck_original(base_rules,path):
    log=[]
    for j,step in enumerate(path["steps"]):
        c=base_rules[step["rule"]-1]
        if len(c["calls"])!=1 or c["head_name"]!="Inv":
            raise RuntimeError("CERTIFICATE_RULE_KIND_MISMATCH")
        u=fresh(base_rules,step["rule"]-1,20000+j)
        pre=[z3.IntVal(x) for x in path["states"][j]]
        post=[z3.IntVal(x) for x in path["states"][j+1]]
        v=z3.Solver()
        v.set(timeout=1200)
        v.add(edge(pre,post,u))
        result=str(v.check())
        log.append({"rule":step["rule"],"status":result})
        if result!="sat":raise RuntimeError("PROOF_REPLAY_REJECTED_STEP_"+str(j))
    init=[z3.IntVal(x) for x in path["states"][0]]
    start_rule=next(c for c in base_rules if len(c["calls"])==0 and c["head_name"]=="Inv")
    initial=fresh(base_rules,start_rule["id"]-1,29990)
    f=z3.Solver()
    f.add(*(list(initial["guard"])+[initial["head"].arg(j)==init[j] for j in range(8)]))
    if f.check()!=z3.sat:raise RuntimeError("PROOF_REPLAY_INITIAL_NOT_ENTAILED")
    error_state=[z3.IntVal(x) for x in path["states"][-1]]
    false_rules=[c for c in base_rules if c["head_name"]=="CHC_COMP_FALSE"]
    triggering=[]
    for c in false_rules:
        u=fresh(base_rules,c["id"]-1,29991+c["id"])
        s=z3.Solver();s.set(timeout=1200)
        s.add(*u["guard"])
        for a in u["calls"]:
            s.add(*[a.arg(j)==error_state[j] for j in range(8)])
        if s.check()==z3.sat:triggering.append(c["id"])
    if not triggering:raise RuntimeError("PROOF_REPLAY_ERROR_CONDITION_FALSE")
    terminators=[c for c in base_rules if z3.is_false(c["head"])]
    if not any(any(a.decl().name()=="CHC_COMP_FALSE" for a in c["guard"]) for c in terminators):
        raise RuntimeError("PROOF_REPLAY_NO_FALSE_CONSEQUENCE")
    return {"initial_rule":start_rule["id"],"step_rule_checks":log,
            "error_rules":triggering,"false_rule_indices":[c["id"] for c in terminators],
            "verified":True}

def main():
    started=time.monotonic()
    report={"name":"FGSR original exact finite derivation attack before more learning",
            "source_sha256":SOURCE_SHA,"scope":"SINGLE_PREMISE_ONLY_UNDERAPPROXIMATION",
            "source_modified":False,"neural_calls":0,"global_Q":"Q1-Q7 OPEN",
            "status":"BLOCKED","max_depth":MAX_DEPTH,
            "solver_wall_cap_ms":CAP_MS,"z3_version":z3.get_version_string()}
    try:
        url=f"https://raw.githubusercontent.com/chc-comp/chc-comp26-benchmarks/{REV}/{ORIGINAL}"
        with urllib.request.urlopen(url,timeout=25) as resp:raw=resp.read()
        if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:raise ValueError("PINNED_ORIGINAL_ID_MISMATCH")
        clauses=original_clauses(raw.decode())
        base=[c for c in clauses if len(c["calls"])==0 and c["head_name"]=="Inv"]
        single=[c for c in clauses if len(c["calls"])==1 and c["head_name"]=="Inv"]
        multi=[c for c in clauses if len(c["calls"])>1]
        if len(base)!=1:raise ValueError("BASE_RULE_COUNT_UNSUPPORTED")
        report.update({"original_rules":len(clauses),"initial_fact_rules":[c["id"] for c in base],
                       "single_premise_rules":len(single),"multi_premise_skipped":len(multi),
                       "source_digest_verified":True})
        init=fresh(clauses,base[0]["id"]-1,10000)
        state=[[z3.Int(f"state_{d}_{i}") for i in range(8)] for d in range(MAX_DEPTH+1)]
        which=[z3.Int(f"rule_{d}") for d in range(MAX_DEPTH)]
        solver=z3.Solver();solver.set(timeout=CAP_MS)
        solver.add(*init["guard"])
        solver.add(*[state[0][j]==init["head"].arg(j) for j in range(8)])
        # This fixed seed is authorized because the initial ORIGINAL Horn
        # universally includes all shared data values; concrete zero is allowed.
        solver.add(*[state[0][i]==0 for i in range(3)])
        evidence=None;depth_reached=0
        sampled=[]
        for depth in range(MAX_DEPTH+1):
            remaining=CAP_MS-int((time.monotonic()-started)*1000)
            if remaining<=0:
                report["status"]="INCOMPLETE_TIME_CAP"
                break
            solver.set(timeout=max(100,remaining))
            solver.push()
            solver.add(z3.Or(state[depth][3]==0,state[depth][3]==1))
            r=solver.check()
            solver.pop()
            sampled.append({"depth":depth,"result":str(r)})
            if r==z3.sat:
                solver.push()
                solver.add(z3.Or(state[depth][3]==0,state[depth][3]==1))
                if solver.check()!=z3.sat:raise RuntimeError("NONREPRODUCIBLE_SAT_SAME_SOLVER")
                model=solver.model()
                path={
                    "states":[triple_to_list(state[j],model) for j in range(depth+1)],
                    "steps":[{"rule":model.eval(which[j],model_completion=True).as_long()} for j in range(depth)]
                }
                solver.pop()
                reverified=recheck_original(clauses,path)
                report.update({"status":"ORIGINAL_UNSAT_CERTIFIED_CONCRETE_HORN_DERIVATION",
                               "counterexample_depth":depth,"certificate":path,
                               "independent_each_original_rule_replay":reverified})
                evidence=True
                break
            if r==z3.unknown:
                report["status"]="INCOMPLETE_SOLVER_UNKNOWN"
                break
            depth_reached=depth
            if depth==MAX_DEPTH:
                report["status"]="BOUNDED_NO_TRACE_NOT_SAFETY_PROOF"
                break
            options=[]
            for c in single:
                u=fresh(clauses,c["id"]-1,depth)
                options.append(z3.And(which[depth]==c["id"],edge(state[depth],state[depth+1],u)))
            solver.add(z3.Or(*options))
        report["depths_checked"]=len(sampled)
        report["highest_depth_unsat"]=depth_reached
        report["per_depth_verdicts"]=sampled
    except Exception as exc:
        report["status"]="BLOCKED_OR_ENGINEERING_ERROR"
        report["error"]=type(exc).__name__+": "+str(exc)[:850]
    report["elapsed_ms"]=round((time.monotonic()-started)*1000,3)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("ORIGINAL_HORN_DERIVATION",report["status"])
    print("DEPTH_CHECKED",report.get("depths_checked"),"REPLAY",report.get("independent_each_original_rule_replay",{}).get("verified",False))
    print("LEARNED_Q",report["global_Q"])

if __name__=="__main__":main()
