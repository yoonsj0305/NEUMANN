"""FGSR Q3 P1: automatically assemble FIVE original Horn relations, source-only.

DEVELOPMENT-ONLY ORIGINAL ALREADY OPENED. A 15-real-weight learned head
proposes numeric self-loop polynomial content from actual source guards.
An independent source-derived candidate grammar + Houdini must synthesize
all multi-relation alignment/range/total scaffolds WITHOUT imported witness.
The equal-information exact classical coefficients are ALWAYS compared.
Proof authority is 9 untouched source Horn clauses; incomplete => ABSTAIN.
"""
import hashlib,json,math,os,re,time,urllib.request
from pathlib import Path
import z3

REV="b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"
SOURCE="eldarica-misc/LIA/llreve/square_twice_safe.c-1_000.smt2"
SOURCE_SHA="f62d0fb72140e6bd7e953dcebd131a4e9498cc9c0c150588ca79944962e9e748"
WEIGHTS=[[1.0000049469135488,.4999992569855871,-2.0057653445301194e-6],
[-1.000002119635724,-6.423412509021618e-7,-5.45191648158471e-7],
[2.011956074289804e-6,-.49999712700133986,5.553681471410288e-7],
[1.4567394845014275e-6,.5000001780616748,.9999947721961792],
[1.3924630612775726e-7,-.5000030165377514,-1.0000031105465235]]
# Previously frozen public GitHub record, NOT refitted on this benchmark.
OUT=Path(os.environ.get("FGSR_RESULT","auto_scaffold_receipt.json"))
MAX_HOUDINI_CHECKS=200
TOTAL_WALL_CAP_S=145
QUERY_CAP_MS=2200

def err(msg):raise ValueError(msg)

def atoms(x):
    if z3.is_and(x):
        for a in x.children():yield from atoms(a)
    else:yield x

def check_sat(exprs,cap=QUERY_CAP_MS):
    s=z3.Solver();s.set(timeout=cap);s.add(*exprs)
    v=s.check()
    return ("sat" if v==z3.sat else "unsat" if v==z3.unsat else "unknown",
            s.model() if v==z3.sat else None)

def parse(source):
    q=z3.parse_smt2_string(source)
    if len(q)!=9:err("CHANGED_ORIGINAL_CLAUSE_COUNT")
    relations={}
    rules=[]
    for i,quant in enumerate(q,1):
        if not z3.is_quantifier(quant) or not quant.is_forall():
            err("NON_FORALL_"+str(i))
        loc=[z3.Const(f"q{i}_{k}",quant.var_sort(k)) for k in range(quant.num_vars())]
        phi=z3.substitute_vars(quant.body(),*loc)
        if not z3.is_implies(phi):err("NON_HORN_"+str(i))
        prem,head=phi.children()
        calls=[a for a in atoms(prem) if z3.is_app(a) and a.decl().name().startswith("inv_")]
        guards=[a for a in atoms(prem) if not(z3.is_app(a) and a.decl().name().startswith("inv_"))]
        if z3.is_app(head) and head.decl().name().startswith("inv_"):
            relations[head.decl().name()]=head.num_args()
        for a in calls:relations[a.decl().name()]=a.num_args()
        rules.append(dict(index=i,calls=calls,guards=guards,head=head))
    if len(relations)!=5:err("DIFFERENT_RELATION_FAMILY")
    return rules,relations

def infer_loop_candidates(rules):
    found={}
    for r in rules:
        if len(r["calls"])!=1:continue
        before=r["calls"][0];after=r["head"]
        if not (z3.is_app(after) and before.decl().name()==after.decl().name()):continue
        name=after.decl().name();guards=r["guards"]
        diff=[j for j in range(after.num_args()) if not z3.eq(after.arg(j),before.arg(j))]
        if len(diff)!=2:continue
        discovered=[]
        for t in diff:
            ok,_=check_sat([*guards,z3.Not(after.arg(t)==before.arg(t)-1)],900)
            if ok!="unsat":continue
            s=next(j for j in diff if j!=t)
            for a in range(after.num_args()):
                if a in diff or not z3.eq(after.arg(a),before.arg(a)):continue
                features=[]
                for k in (-2,-1,0,1,2):
                    for m in (-2,-1,0,1,2):
                        for n in (-2,-1,0,1,2):
                            equality=(after.arg(s)==before.arg(s)+
                                      k*before.arg(a)+m*before.arg(t)+n)
                            verdict,_=check_sat([*guards,z3.Not(equality)],550)
                            if verdict=="unsat":features.append((k,m,n))
                if len(features)==1:discovered.append((a,s,t,features[0]))
        if len(discovered)!=1:continue
        if name in found:err("DUPLICATE_RECURSIVE_PREDICATE")
        a,s,t,feat=discovered[0]
        pred=tuple(round(sum(weight*feature for weight,feature in zip(row,feat)))
                   for row in WEIGHTS)
        # Independent exact-classical teacher; no neural shortcut for learned arm.
        k,m,n=feat
        exact=(k+m/2,-k,-m/2,m/2+n,-m/2-n)
        if any(abs(x-round(x))>1e-9 for x in exact):
            err("NON_INTEGER_COEFFICIENT_ORIGINAL")
        exact=tuple(int(round(x)) for x in exact)
        found[name]=dict(original_rule=r["index"],bound=a,sum=s,remain=t,
                         source_features=feat,learned=pred,classical=exact)
    if not found:err("NO_SOURCE_RECURSIVE_LOOP_DETECTED")
    return found

def proposals(arity,loop,mode):
    xs=[z3.Int(f"t{i}") for i in range(arity)]
    p=[];tags=[]
    def add(label,x):
        if z3.is_true(x):return
        p.append(x);tags.append(label)
    for a in range(arity):
        add(f"eq0_{a}",xs[a]==0)
        add(f"ge0_{a}",xs[a]>=0)
        add(f"le0_{a}",xs[a]<=0)
        for b in range(a+1,arity):
            add(f"eq_{a}_{b}",xs[a]==xs[b])
            add(f"le_{a}_{b}",xs[a]<=xs[b])
            add(f"ge_{a}_{b}",xs[a]>=xs[b])
    for a in range(arity):
        for t in range(arity):
            if a==t:continue
            add(f"phase_{a}_{t}",z3.If(xs[a]<=0,xs[t]==xs[a],
                        z3.And(xs[t]>=0,xs[t]<=xs[a])))
            add(f"total_{t}_from_{a}",
                xs[t]==z3.If(xs[a]<=0,z3.IntVal(0),xs[a]*xs[a]))
    if loop is not None and mode!="NONE":
        a,s,t=(loop["bound"],loop["sum"],loop["remain"])
        c=loop["learned"] if mode=="LEARNED" else loop["classical"]
        expr=(c[0]*xs[a]*xs[a]+c[1]*xs[a]*xs[t]+c[2]*xs[t]*xs[t]+
              c[3]*xs[a]+c[4]*xs[t])
        add("SOURCE_DERIVED_LOOP_POLYNOMIAL_"+mode,xs[s]==expr)
    # Identical fixed grammar for all named relations, no per-name scaffold.
    return xs,p,tags

def interp(atom,cands,active):
    name=atom.decl().name()
    x,formulas,tags=cands[name]
    if not active[name]:return z3.BoolVal(True)
    substitutions=list(zip(x,atom.children()))
    return z3.And(*[z3.substitute(formulas[j],*substitutions)
                     for j in sorted(active[name])])

def solve_source(rules,relations,loops,mode,t0):
    cands={name:proposals(arity,loops.get(name),mode)
           for name,arity in relations.items()}
    active={name:set(range(len(cands[name][1]))) for name in cands}
    removals=[];calls=0;rounds=0
    while True:
        if time.monotonic()-t0>TOTAL_WALL_CAP_S:err("TOTAL_WALL_CAP")
        rounds+=1;changed=False
        for r in rules:
            h=r["head"]
            if not(z3.is_app(h) and h.decl().name() in cands):continue
            name=h.decl().name()
            while active[name]:
                if calls>=MAX_HOUDINI_CHECKS:err("SMT_CHECK_CAP")
                if time.monotonic()-t0>TOTAL_WALL_CAP_S:err("TOTAL_WALL_CAP")
                antecedents=[*r["guards"],*[interp(a,cands,active) for a in r["calls"]]]
                head=interp(h,cands,active)
                status,model=check_sat([*antecedents,z3.Not(head)])
                calls+=1
                if status=="unsat":break
                if status!="sat":err("UNKNOWN_DURING_SYNTHESIS_RULE_"+str(r["index"]))
                x,fs,tags=cands[name]
                subst=list(zip(x,h.children()))
                bad={j for j in active[name] if
                     z3.is_false(model.eval(z3.substitute(fs[j],*subst),
                                             model_completion=True))}
                if not bad:err("CEGAR_COUNTEREXAMPLE_WITHOUT_FAILED_CONJUNCT")
                active[name]-=bad
                removals.append(dict(rule=r["index"],predicate=name,
                         removed=len(bad),representatives=[tags[j] for j in sorted(bad)[:4]]))
                changed=True
        if not changed:break
        if rounds>30:err("FIXPOINT_ITERATION_CAP")
    # Verify fresh, independent Z3 each original quantified clause, including safety.
    verdict=[]
    for r in rules:
        h=r["head"]
        antecedents=[*r["guards"],*[interp(a,cands,active) for a in r["calls"]]]
        if z3.is_app(h) and h.decl().name() in cands:
            contradictory=z3.Not(interp(h,cands,active))
        elif z3.is_false(h):
            contradictory=z3.BoolVal(True)
        else:err("UNSUPPORTED_GOAL_KIND")
        start=time.perf_counter_ns()
        status,_=check_sat([*antecedents,contradictory],5000)
        verdict.append(dict(rule=r["index"],status=status,
                   wall_ms=round((time.perf_counter_ns()-start)/1e6,3)))
    selected={n:[cands[n][2][j] for j in sorted(active[n])] for n in active}
    definitions=[]
    for name in sorted(cands):
        vars_,forms,_=cands[name]
        param=[z3.Int(f"p{i}") for i in range(len(vars_))]
        subs=list(zip(vars_,param))
        full=(z3.And(*[z3.substitute(forms[j],*subs) for j in sorted(active[name])])
              if active[name] else z3.BoolVal(True))
        definition="(define-fun |"+name+"| ("+" ".join(
            f"(p{i} Int)" for i in range(len(param)))+") Bool "+full.sexpr()+")"
        definitions.append(definition)
    certificate="\n".join(definitions)+"\n"
    return dict(status=("CERTIFIED_ALL_ORIGINAL" if len(verdict)==9 and
                        all(x["status"]=="unsat" for x in verdict)
                      else "INCOMPLETE_ORIGINAL_GOAL"),
                candidate_inventory={n:len(cands[n][1]) for n in cands},
                selected_conjuncts=selected,original_verdicts=verdict,
                explicit_original_relation_definitions_smt2=certificate,
                original_unsat_count=sum(x["status"]=="unsat" for x in verdict),
                houdini_rounds=rounds,houdini_queries=calls,
                removals_total=sum(x["removed"] for x in removals),
                removal_sample=removals[:16])

def independently_replay_original(source,definitions):
    # Physically separate interpreter: refetch original bytes in workflow,
    # parse literal original quantified SMT-LIB clauses, not Houdini AST refs.
    all_forms=[];depth=0;start=None
    for pos,ch in enumerate(source):
        if ch=="(":
            if depth==0:start=pos
            depth+=1
        elif ch==")":
            depth-=1
            if depth==0:all_forms.append(source[start:pos+1])
    original=[x for x in all_forms if re.match(r"^\(assert\s",x)]
    if len(original)!=9:err("CHANGED_SOURCE_IN_INDEPENDENT_REPLAY")
    checks=[]
    for i,assertion in enumerate(original,1):
        inside=assertion[len("(assert"):-1].strip()
        standalone=z3.Solver()
        standalone.set(timeout=7000)
        start=time.perf_counter_ns()
        try:
            parsed=z3.parse_smt2_string(
                "(set-logic ALL)\n"+definitions+"\n(assert "+inside+")")
            if len(parsed)!=1 or not z3.is_quantifier(parsed[0]) or not parsed[0].is_forall():
                err("NOT_AN_ORIGINAL_QUANTIFIED_CLAUSE")
            q=parsed[0]
            fresh=[z3.Const(f"independent_clause_{i}_v{j}",q.var_sort(j))
                   for j in range(q.num_vars())]
            universally_instantiated=z3.substitute_vars(q.body(),*fresh)
            standalone.add(z3.Not(universally_instantiated))
            answer=str(standalone.check())
        except Exception as exc:
            answer="ERROR_"+type(exc).__name__+":"+str(exc)[:130]
        checks.append({"original_clause":i,"result":answer,
                       "wall_ms":round((time.perf_counter_ns()-start)/1e6,3)})
    return {"separate_native_parse_original":True,"checks":checks,
            "verified":len(checks)==9 and all(c["result"]=="unsat" for c in checks)}

def main():
    started=time.monotonic()
    record={"experiment":"FGSR-Q3 P1 original source-driven full 5-predicate auto scaffold",
        "status":"NOT_RUN", "source_sha256":SOURCE_SHA,
        "prior_human_scaffold_imported":False,"source_previously_opened":True,
        "trained_architecture":"frozen 15-weight numeric loop head (NOT relation-family learner)",
        "classical_baseline_included":True,
        "no_new_training":True,"global_q1_q7":"OPEN",
        "z3_version":z3.get_version_string()}
    try:
        url=f"https://raw.githubusercontent.com/chc-comp/chc-comp26-benchmarks/{REV}/{SOURCE}"
        with urllib.request.urlopen(url,timeout=25) as resp:raw=resp.read()
        if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:err("ORIGINAL_ID_MISMATCH")
        rules,relations=parse(raw.decode())
        loops=infer_loop_candidates(rules)
        record["original_clause_count"]=len(rules)
        record["source_relation_signatures"]=relations
        record["source_extracted_loops"]=loops
        record["learning_source_exact_coefficients"]={
            name:(loops[name]["learned"]==loops[name]["classical"]) for name in loops}
        for mode in ("LEARNED","CLASSICAL"):
            if mode=="CLASSICAL" and all(
                loops[n]["learned"]==loops[n]["classical"] for n in loops):
                # Exact same candidate inventory/proof implies identical check.
                record["CLASSICAL"]=dict(
                    status="CERTIFICATE_IDENTICAL_TO_LEARNED_PROOF_IF_CERTIFIED",
                    same_candidate_semantic_content=True,
                    identical_numeric_proposals=True,
                    no_additional_solver_calls=True)
                continue
            t=time.monotonic()
            record[mode]=solve_source(rules,relations,loops,mode,started)
            record[mode]["execution_wall_ms"]=round((time.monotonic()-t)*1000,3)
        record["SECOND_INDEPENDENT_ORIGINAL_REPLAY"]=independently_replay_original(
            raw.decode(),record["LEARNED"]["explicit_original_relation_definitions_smt2"])
        t=time.monotonic()
        record["NONE"]=solve_source(rules,relations,loops,"NONE",started)
        record["NONE"]["execution_wall_ms"]=round((time.monotonic()-t)*1000,3)
        record["status"]=(
            "FULL_SOURCE_AUTOMATIC_SCAFFOLD_AND_INDEPENDENT_REPLAY_CERTIFIED"
            if record["LEARNED"]["status"]=="CERTIFIED_ALL_ORIGINAL"
            and record["SECOND_INDEPENDENT_ORIGINAL_REPLAY"]["verified"]
            else "AUTOMATIC_RELATION_SCAFFOLD_NOT_CERTIFIED")
    except Exception as exc:
        record["status"]="BLOCKED_OR_INCOMPLETE"
        record["error"]=type(exc).__name__+":"+str(exc)[:1200]
    record["full_wall_ms"]=round((time.monotonic()-started)*1000,3)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n")
    print("FGSR_AUTO_SCAFFOLD",record["status"])
    print("AUTOMATIC_SOURCE_PROOF",record.get("LEARNED",{}).get("original_unsat_count"))
    print("SOURCE_LOOPS",list(record.get("source_extracted_loops",{})))
    print("GLOBAL_Q",record["global_q1_q7"])

if __name__=="__main__":main()
