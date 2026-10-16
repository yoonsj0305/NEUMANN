"""One bounded Houdini conjunctive abstract interpretation on an OPENED authentic
48-clause Horn source. Researcher-provided hypothesis predicates; NO learned model.
Excludes all result-driven replacement predicates. Every original clause checked.
"""
import hashlib,json,os,re,time,urllib.request
from pathlib import Path
from manual_control_proof_once import split_top,INV_RE,FALSE_RE,check,SHA,REPO,REV,SOURCE

OUT=Path(os.environ.get("FGSR_RESULT","houdini_receipt.json"))
NAMES=[
    "pc5_eq_minus1",
    "pc6_eq_minus1",
    "main_pc_range_0_to_4",
    "main_activated_implies_shared_a_zero",
    "before_main_4_worker_pcs_minus1",
    "worker_pc0_finite_safe_states",
    "worker_pc1_finite_safe_states"
]
ALLOWED=(-1,2,4,5,6,7,8)

def part(k,args):
    a,b,c,d,e,f,g,h=args
    neg=lambda v:f"(= {v} (- 1))"
    in_set=lambda v:"(or "+" ".join(f"(= {v} {x})" if x>=0 else neg(v) for x in ALLOWED)+")"
    return [
        neg(f),
        neg(g),
        "(or "+" ".join(f"(= {h} {i})" for i in range(5))+")",
        f"(=> (not (= {h} 0)) (= {a} 0))",
        f"(=> (not (= {h} 4)) (and {neg(d)} {neg(e)}))",
        in_set(d),
        in_set(e),
    ][k]

def conjunction(args,candidates):
    return "true" if not candidates else "(and "+" ".join(part(i,args) for i in candidates)+")"

def replace_rule(assertion,candidates,one_head=None):
    form=assertion[len("(assert"):-1].strip()
    occurrences=list(INV_RE.finditer(form))
    if not occurrences:
        if "CHC_COMP_FALSE" not in form:raise ValueError("no original relation")
    head_index=None
    if occurrences:
        last=occurrences[-1]
        # Original Horn normal form: last Inv is the conclusion exactly when
        # only closing parentheses follow that atom.
        if form[last.end():].strip(" \n\t\r)")=="":head_index=len(occurrences)-1
    chunks=[];pos=0
    for j,atom in enumerate(occurrences):
        chunks.append(form[pos:atom.start()])
        args=atom.group(1).split()
        chunks.append(
            part(one_head,args) if j==head_index and one_head is not None
            else conjunction(args,candidates)
        )
        pos=atom.end()
    chunks.append(form[pos:])
    translated=FALSE_RE.sub("false","".join(chunks))
    if INV_RE.search(translated) or "CHC_COMP_FALSE" in translated:raise ValueError("incomplete_substitution")
    return translated,head_index

def main():
    t0=time.perf_counter_ns()
    result={
        "name":"NEUMANN FSGR opened 48-Horn classical Houdini abstract interpretation",
        "scope":"FINITE_RESEARCHER_HYPOTHESIS_BASIS_NOT_LEARNED",
        "neural_calls":0,"Q1_Q7":"OPEN",
        "original_sha256":SHA,"status":"BLOCKED",
        "hypothesis_families":NAMES,"counterexamples":[],
        "original_modified":False
    }
    try:
        u=f"https://raw.githubusercontent.com/{REPO}/{REV}/{SOURCE}"
        with urllib.request.urlopen(u,timeout=35) as f:raw=f.read()
        if hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError("SOURCE_IDENTITY_ERROR")
        forms=split_top(raw.decode())
        rules=[x for x in forms if re.match(r"^\(assert\s",x)]
        if len(rules)!=48:raise ValueError("ORIGINAL_CLAUSE_COUNT_CHANGED")
        heads=[]
        for ix,rule in enumerate(rules,1):
            _,hi=replace_rule(rule,set(range(len(NAMES))),one_head=0)
            heads.append(hi is not None)
        if sum(heads)!=45 or heads[-3:]!=[False,False,False]:
            raise ValueError("HORN_HEAD_SHAPE_CHANGED:"+str(heads))
        active=set(range(len(NAMES)))
        max_iters=len(NAMES)+1
        attempts=0
        iterations=[]
        for loop in range(max_iters):
            drop=[]
            tested=0
            for k in sorted(active):
                for ri,rule in enumerate(rules):
                    if not heads[ri]:continue
                    formula,_=replace_rule(rule,active,one_head=k)
                    tested+=1;attempts+=1
                    obs=check(formula)
                    if obs["status"]=="sat":
                        drop.append((k,ri+1))
                        break
                    if obs["status"]!="unsat":
                        raise RuntimeError("unknown_or_error_in_houdini:"+str((k,ri+1,obs)))
            iteration={"iteration":loop+1,"survived_before":[NAMES[i] for i in sorted(active)],
                       "removed":[{"predicate":NAMES[k],"first_breaking_original_rule":ri} for k,ri in drop],
                       "independence_checks":tested}
            iterations.append(iteration)
            if not drop:break
            for k,ri in drop:active.remove(k)
        else:raise ValueError("HOUDINI_ITERATION_CAP")
        result["iterations"]=iterations
        result["accepted_inductive_conjuncts"]=[NAMES[k] for k in sorted(active)]
        result["hints_eliminated"]=[NAMES[k] for k in range(len(NAMES)) if k not in active]
        result["candidate_examinations"]=attempts
        result["original_rule_checks"]=[]
        for ri,rule in enumerate(rules,1):
            formula,_=replace_rule(rule,active,one_head=None)
            obs=check(formula)
            result["original_rule_checks"].append({"rule":ri, "status":obs["status"]})
        result["full_original_unsat_count"]=sum(v["status"]=="unsat" for v in result["original_rule_checks"])
        result["first_original_fail"]=next((v for v in result["original_rule_checks"] if v["status"]!="unsat"),None)
        result["status"]=(
            "ALL_48_ORIGINAL_CERTIFIED_CLASSICAL_CONJUNCTIVE"
            if result["full_original_unsat_count"]==48 else
            "GREATEST_BASIS_INVARIANT_INSUFFICIENT_FOR_ORIGINAL"
        )
    except Exception as exc:
        result["status"]="BLOCKED_OR_ERROR"
        result["error"]=type(exc).__name__+": "+str(exc)[:800]
    result["wall_ms"]=round((time.perf_counter_ns()-t0)/1e6,3)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("HOUDINI_GATE",result["status"])
    print("INDUCTIVE_SURVIVORS",result.get("accepted_inductive_conjuncts"))
    print("ALL_ORIGINAL",result.get("full_original_unsat_count"),"of 48")
    print("NEUMANN_Q1_Q7",result["Q1_Q7"])
if __name__=="__main__":main()
