"""Bounded known Houdini invariant inference and CVC5 SyGuS merge proposals.

Uses only the public fold. Same verifier as every other proposer. This prototype
is not full Synduce, a learned engine, or proof of strongest baseline performance.
"""
from time import perf_counter
from neumann1.recursive_summary import (SummaryError, program, validate_problem, cvc_program,
                                       interpret, obligations, check_summary)


def conjunction(terms):
    if not terms:return True
    value=terms[0]
    for term in terms[1:]:value=["and",value,term]
    return value


def infer_invariant(problem,timeout_ms=1000):
    import cvc5
    from cvc5 import Kind
    d=validate_problem(problem)
    names=[f"z{i}" for i in range(d)]
    candidates=[["ge",z,0] for z in names]+[["le",z,0] for z in names]
    candidates += [["ge",a,b] for a in names for b in names if a!=b]
    active=[c for c in candidates if interpret(program(names,[c]),problem["empty"])[0]]
    tm=cvc5.TermManager()
    z=[tm.mkConst(tm.getIntegerSort(),name) for name in names]
    head=tm.mkConst(tm.getIntegerSort(),"head")
    after=cvc_program(tm,problem["step"],[head]+z)
    rejected=[]
    rounds=0
    while active:
        rounds+=1
        pre=cvc_program(tm,program(names,[conjunction(active)]),z)[0]
        remove=[]
        for predicate in active:
            solver=cvc5.Solver(tm);solver.setLogic("QF_LIA");solver.setOption("tlimit-per",str(timeout_ms))
            post=cvc_program(tm,program(names,[predicate]),after)[0]
            solver.assertFormula(tm.mkTerm(Kind.AND,pre,tm.mkTerm(Kind.NOT,post)))
            result=solver.checkSat()
            if not result.isUnsat():
                remove.append(predicate)
                rejected.append({"predicate":predicate,"status":str(result),"round":rounds})
        if not remove:break
        active=[c for c in active if c not in remove]
    return program(names,[conjunction(active)]),{"rounds":rounds,"retained":len(active),"rejected":rejected}


def term_expression(term):
    from cvc5 import Kind
    if term.isIntegerValue():return int(term.getIntegerValue())
    if term.isBooleanValue():return term.getBooleanValue()
    if term.getKind() in {Kind.VARIABLE,Kind.CONSTANT} and term.hasSymbol():return term.getSymbol()
    ops={Kind.ADD:"add",Kind.SUB:"sub",Kind.GEQ:"ge",Kind.LEQ:"le",Kind.GT:"gt",Kind.LT:"lt",
         Kind.EQUAL:"eq",Kind.AND:"and",Kind.OR:"or",Kind.NOT:"not",Kind.ITE:"ite"}
    if term.getKind()==Kind.APPLY_UF and term[0].hasSymbol() and term[0].getSymbol()=="summary_max":
        return ["max",term_expression(term[1]),term_expression(term[2])]
    if term.getKind()==Kind.NEG:return ["sub",0,term_expression(term[0])]
    if term.getKind() not in ops:raise SummaryError("Native synthesized unsupported constructor")
    items=[term_expression(term[i]) for i in range(term.getNumChildren())]
    op=ops[term.getKind()]
    if op in {"add","and","or"} and len(items)>2:
        value=items[0]
        for item in items[1:]:value=[op,value,item]
        return value
    return [op]+items


def propose(problem,timeout_ms=5000,checkpoint=None):
    import cvc5
    from cvc5 import Kind
    if type(timeout_ms)is not int or not 1<=timeout_ms<=10000:raise SummaryError("Bounded synthesis timeout required")
    start=perf_counter()
    d=validate_problem(problem)
    invariant,inference=infer_invariant(problem)
    if checkpoint:checkpoint({"phase":"invariants inferred","invariant":invariant,"inference":inference})
    z=[f"z{i}" for i in range(d)]
    def rename(t):
        if isinstance(t,str) and t.startswith("r") and t[1:].isdigit():return "z"+t[1:]
        return [rename(c) for c in t] if isinstance(t,list) else t
    proposal={"empty":list(problem["empty"]),"step":program(["head"]+z,[rename(t) for t in problem["step"]["outputs"]]),
              "merge":program([f"l{i}" for i in range(d)]+[f"r{i}" for i in range(d)],[0]*d),
              "decode":program(z,z),"invariant":invariant}
    tm=cvc5.TermManager();solver=cvc5.Solver(tm)
    solver.setOption("sygus","true");solver.setOption("tlimit-per",str(timeout_ms));solver.setLogic("LIA")
    integer=tm.getIntegerSort()
    args=[tm.mkVar(integer,n) for n in proposal["merge"]["inputs"]]
    mx,my=tm.mkVar(integer,"mx"),tm.mkVar(integer,"my")
    max_fun=solver.defineFun("summary_max",[mx,my],integer,tm.mkTerm(Kind.ITE,tm.mkTerm(Kind.GEQ,mx,my),mx,my))
    functions=[]
    for i in range(d):
        nt=tm.mkVar(integer,f"Start{i}")
        grammar=solver.mkGrammar(args,[nt])
        features=[tm.mkInteger(0)]+args+[tm.mkTerm(Kind.ADD,a,b) for j,a in enumerate(args) for b in args[j:]]
        grammar.addRules(nt,features+[tm.mkTerm(Kind.APPLY_UF,max_fun,nt,nt)])
        functions.append(solver.synthFun(f"merge{i}",args,integer,grammar))
    def merge(left,right):return [tm.mkTerm(Kind.APPLY_UF,f,*(left+right)) for f in functions]
    formulas,_=obligations(tm,problem,proposal,merge_override=merge,
                           symbol_factory=lambda name:solver.declareSygusVar(name,integer))
    for _,formula in formulas:solver.addSygusConstraint(formula)
    result=solver.checkSynth()
    record={"status":str(result),"invariant_inference":inference,"synthesis_seconds":perf_counter()-start,
            "source":"public fold only","full_Synduce":False,"learned":False,
            "grammar":"fixed reference-state width,public variables,pairwise sums,0,recursive max"}
    if not result.hasSolution():return {**record,"proposal":None,"accepted":False}
    solutions=[solver.getSynthSolution(f) for f in functions]
    record["solution_terms"]=[str(s) for s in solutions]
    proposal["merge"]=program(proposal["merge"]["inputs"],[term_expression(s[1]) for s in solutions])
    if checkpoint:checkpoint({"phase":"proposal synthesized,not yet certified","record":record,"proposal":proposal})
    certificate=check_summary(problem,proposal)
    return {**record,"proposal":proposal,"certificate":certificate,"accepted":certificate["accepted"]}
