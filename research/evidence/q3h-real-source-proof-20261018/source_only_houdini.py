"""Q3H-2: source-and-goal ONLY classical Houdini for authentic C loops.

Does NOT read the workbook or any published invariant; output candidates from
the source AST, program constants, typed variables, and branching guards.
Classical symbolic candidate elimination, 32-bit arithmetic overflow checks.
Neural training/inference zero; originals are previously OPENED development.
"""
from __future__ import annotations
import argparse,collections,hashlib,io,json,time,zipfile
from pathlib import Path

import z3
from pycparser import c_ast

from replay_real_c_loop_invariants import (
    as_boolean,check,evaluate,get_main,model_original,signed_domain,
    MIN_INT,MAX_INT,Unsupported,
)
SOURCES={
 "dataset/loop_invariants/LinearArbitrary-SeaHorn/VeriMAP/TRACER-testabs7_VeriMAP_true.c":
 "82a2f45ee5ab237a1e78961dbb768b13da71fc55b7832f937ce671a8293a606b",
 "dataset/loop_invariants/LinearArbitrary-SeaHorn/invgen/simple.c":
 "704ad724dfc48ff1944cb92f26ab6cef8f4297578cf2e16c8070b56fe9b84071",
 "dataset/loop_invariants/LinearArbitrary-SeaHorn/sharma_splitter/popl.c":
 "b831e286e1be53b6c59761b073ee2e8e166f3e38b0ba6525a433d667e898c767",
}
KEYS=tuple(SOURCES)

def syntax_features(source,loop_state):
    fn,_=get_main(source)
    constants={-1,0,1}
    predicates=[]
    class Visitor(c_ast.NodeVisitor):
        def visit_Constant(self,node):
            if node.type=="int":
                try:
                    val=int(node.value,0)
                    if abs(val)<=10000:constants.add(val)
                except ValueError:pass
        def visit_If(self,node):
            # Real source branch guards only, no guessed label grammar.
            try:
                cond=as_boolean(evaluate(node.cond,loop_state))
                predicates.append(cond)
            except Unsupported:pass
            self.generic_visit(node)
    Visitor().visit(fn)
    return sorted(constants),predicates

def pool(source,states):
    names=sorted(states)
    literals,predicates=syntax_features(source,states)
    atom=[]
    for name in names:
        var=states[name]
        for constant in literals:
            for op,value in ((">=",var>=constant),
                             ("<=",var<=constant),
                             ("==",var==constant)):
                atom.append((f"{name}{op}{constant}",value))
    for i,name in enumerate(names):
        for other in names[i+1:]:
            x,y=states[name],states[other]
            atom.extend([(f"{name}<={other}",x<=y),
                         (f"{name}>={other}",x>=y),
                         (f"{name}=={other}",x==y)])
    out=list(atom)
    # Guarded statements represent cross-variable inductive facts even when
    # unconditional facts do NOT hold. Guard comes from ORIGINAL source IFs.
    for index,guard in enumerate(predicates):
        for desc,condition in atom:
            out.append((f"if{index}_then_{desc}",z3.Implies(guard,condition)))
            out.append((f"if{index}_else_{desc}",z3.Implies(z3.Not(guard),condition)))
    seen=set();dedup=[]
    for label,expr in out:
        exprkey=z3.simplify(expr).sexpr()
        if exprkey not in seen:
            seen.add(exprkey);dedup.append((label,expr))
    if len(dedup)>500:
        raise Unsupported("CANDIDATE_BUDGET_EXCEEDED")
    return dedup,{"source_numeric_literals":literals,
                  "source_branch_guards":len(predicates)}

def subst(expr,mapping):
    return z3.substitute(expr,*[(before,after) for before,after in mapping])

def candidate_proof(source):
    # Original program syntax and original goal only. The public Loopy
    # invariant is deliberately not opened, parsed, imported or used.
    model=model_original(source,"1")
    names=tuple(sorted(model["loop_state"]))
    candidates,features=pool(source,model["loop_state"])
    before=model["loop_state"]
    afterpre=model["after_prelude"]
    body=model["body_state"]
    replacement_init=[(before[k],afterpre[k]) for k in names]
    replacement_after=[(before[k],body[k]) for k in names]
    from_init=z3.And(*signed_domain(model["initial"]),*model["init_assumptions"])
    from_loop=z3.And(*signed_domain(before))
    guard=model["loop_test"]

    t0=time.perf_counter_ns()
    # Every candidate must hold after the real source's initialization.
    usable=[]
    for desc,term in candidates:
        initexpr=subst(term,replacement_init)
        res=check(z3.And(from_init,z3.Not(initexpr)),timeout=1300)
        if res=="unsat":usable.append((desc,term))
    initial_keep=len(usable)
    iteration=0
    total_checks=len(candidates)
    while True:
        if iteration>=len(candidates)+1:raise Unsupported("HOUDINI_NONTERMINATION")
        iteration+=1
        theory=z3.And(*[p for _,p in usable])
        prefix=z3.And(from_loop,theory,guard)
        drop=set()
        for label,term in usable:
            post=subst(term,replacement_after)
            res=check(z3.And(prefix,z3.Not(post)),timeout=1300)
            total_checks+=1
            if res!="unsat":drop.add(label)
        if not drop:break
        usable=[(label,t) for label,t in usable if label not in drop]
    theorem=z3.And(*[t for _,t in usable])
    prefix=z3.And(from_loop,theorem)
    # Independent final checks from scratch (NOT Houdini selection verdict).
    base=check(z3.And(from_init,z3.Not(subst(theorem,replacement_init))))
    inductive=check(z3.And(prefix,guard,z3.Not(subst(theorem,replacement_after))))
    original_goal=check(z3.And(prefix,z3.Not(guard),z3.Not(model["post_assert"])))
    known_range=check(z3.And(prefix,guard,z3.Or(*[
        z3.Or(x<MIN_INT,x>MAX_INT) for x in model["arithmetic_expressions"]
    ]))) if model["arithmetic_expressions"] else "unsat"
    # A manually strengthened/mutated goal must be rejected.
    falsified_goal=check(z3.And(prefix,z3.Not(guard)))
    no_invariant_goal=check(z3.And(from_loop,z3.Not(guard),z3.Not(model["post_assert"])))
    verified=(len(usable)>0 and
              all(t=="unsat" for t in (base,inductive,original_goal,known_range))
              and falsified_goal=="sat" and no_invariant_goal=="sat")
    return {
        "status":"SOURCE_ONLY_AUTO_INVARIANT_CERTIFIED" if verified
                 else "SOURCE_ONLY_AUTO_INVARIANT_NOT_PROVEN",
        "source_conditioned_candidate_count":len(candidates),
        "initial_surviving_candidates":initial_keep,
        "final_inductive_candidate_count":len(usable),
        "houdini_fixpoint_iterations":iteration,
        "total_induction_solver_queries":total_checks,
        "generated_candidate_formula_hashes":[hashlib.sha256(t.sexpr().encode()).hexdigest()
                                              for _,t in usable],
        "inductive_source_candidate_names":[label for label,_ in usable],
        "full_original_check":{"initial":base,"inductive":inductive,
          "postcondition":original_goal,"signed_overflow":known_range,
          "deliberately_false_goal":falsified_goal,
          "empty_invariant_goal":no_invariant_goal},
        "program_features_used":features,
        "wall_ms":round((time.perf_counter_ns()-t0)/1e6,3),
        "learned_model_calls":0,
        "published_invariant_label_read":False,
        "human_added_source_specific_lemmas":False,
        "limited_source_conditioned_classical_grammar":True,
    }

def run(original_archive):
    receipt={"status":"Q3H2_SOURCE_ONLY_CLASSICAL_SOURCE_CONDITIONED_INVARIANT_SEARCH",
      "source_kind":"authentic Microsoft Loopy C source, already opened in Q3H",
      "source_revision":"91fe89245a0894ec8ad3741d85ae91ce3b552b2e",
      "public_published_labels_read":False,"q3f_holdout_read":False,
      "neural_learning_calls":0,"global_q1_q7":"OPEN",
      "records":[]}
    with zipfile.ZipFile(original_archive) as z:
        for name,expected_sha in SOURCES.items():
            raw=z.read(name)
            if hashlib.sha256(raw).hexdigest()!=expected_sha:
                raise ValueError("EXACT_AUTHENTIC_SOURCE_MISMATCH")
            code=raw.decode("utf-8")
            try:
                result=candidate_proof(code)
            except Exception as e:
                result={"status":"BLOCKED_OR_UNSUPPORTED",
                        "error":f"{type(e).__name__}: {str(e)[:180]}",
                        "learned_model_calls":0}
            receipt["records"].append({"source_path":name,"source_sha256":expected_sha,"proof":result})
    receipt["classically_proven"]=sum(r["proof"]["status"]=="SOURCE_ONLY_AUTO_INVARIANT_CERTIFIED"
                                    for r in receipt["records"])
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dataset",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    r=run(a.dataset)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2)+"\n")
    print("Q3H2_REAL_SOURCE_ONLY_CLASSICAL_HOUDINI",
          [(x["source_path"],x["proof"]["status"],
             x["proof"].get("final_inductive_candidate_count"))
           for x in r["records"]])
    print("FULL_ORIGINAL_PROVEN",r["classically_proven"],"OF",len(r["records"]))
    print("Q1_Q7",r["global_q1_q7"])
