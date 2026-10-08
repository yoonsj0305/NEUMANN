"""Generated list summaries with exact SMT checks of a sufficient induction rule.

Piecewise linear integers only. Solver UNSAT is trusted; no independently
checkable proof kernel is claimed. This implements verification,not learning.
The reference fold is preserved on every finite integer list. List concatenation
must preserve order. Compiler/checker rights belong equally to native and learned
proposers. UNKNOWN or a counterexample never authorizes execution.
"""
from copy import deepcopy
import hashlib
import json
from time import perf_counter


class SummaryError(ValueError):
    pass


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


OPS = {"add": ("Int", "Int", "Int"), "sub": ("Int", "Int", "Int"),
       "max": ("Int", "Int", "Int"), "min": ("Int", "Int", "Int"),
       "ge": ("Int", "Int", "Bool"), "le": ("Int", "Int", "Bool"),
       "gt": ("Int", "Int", "Bool"), "lt": ("Int", "Int", "Bool"),
       "eq": ("Int", "Int", "Bool"), "and": ("Bool", "Bool", "Bool"),
       "or": ("Bool", "Bool", "Bool"), "not": ("Bool", "Bool"),
       "ite": ("Bool", "Int", "Int", "Int")}


def validate_program(program, expected=None, max_nodes=4096, max_depth=64):
    if not isinstance(program, dict) or set(program) != {"semantics", "inputs", "outputs"} or program["semantics"] != "exact_piecewise_linear_integer":
        raise SummaryError("Strict piecewise-linear public program schema required")
    inputs, outputs = program["inputs"], program["outputs"]
    if not isinstance(inputs, list) or len(inputs)>32 or any(not isinstance(s,str) or not s.isidentifier() for s in inputs) or len(set(inputs))!=len(inputs):
        raise SummaryError("Bounded unique input interface required")
    if not isinstance(outputs,list) or not 1<=len(outputs)<=8:
        raise SummaryError("Bounded ordered output interface required")
    remaining = [max_nodes]
    def infer(term, depth):
        remaining[0] -= 1
        if remaining[0]<0 or depth>max_depth:
            raise SummaryError("Expression resource budget exceeded")
        if type(term) is int and -(2**63)<=term<2**63:
            return "Int"
        if type(term) is bool:
            return "Bool"
        if isinstance(term,str) and term in inputs:
            return "Int"
        if not isinstance(term,list) or not term or not isinstance(term[0],str) or term[0] not in OPS:
            raise SummaryError("Unregistered constructor or variable")
        signature = OPS[term[0]]
        if len(term) != len(signature) or [infer(t,depth+1) for t in term[1:]] != list(signature[:-1]):
            raise SummaryError("Expression type/arity mismatch")
        return signature[-1]
    types = [infer(t,0) for t in outputs]
    if expected is not None and types != expected:
        raise SummaryError("Output type mismatch")
    return types


def program(inputs, outputs):
    return {"semantics":"exact_piecewise_linear_integer", "inputs":list(inputs), "outputs":list(outputs)}


def validate_problem(problem):
    if not isinstance(problem,dict) or set(problem)!={"semantics","empty","step"} or problem["semantics"]!="integer_list_right_fold":
        raise SummaryError("Original public fold only; no Oracle/labels/constraints")
    empty=problem["empty"]
    if not isinstance(empty,list) or not 1<=len(empty)<=8 or any(type(v)is not int or not -(2**63)<=v<2**63 for v in empty):
        raise SummaryError("Bounded exact empty reference state required")
    validate_program(problem["step"],["Int"]*len(empty))
    if problem["step"]["inputs"] != ["head"]+[f"r{i}" for i in range(len(empty))]:
        raise SummaryError("Original ordered fold state interface required")
    return len(empty)


def validate_proposal(problem,proposal):
    width=validate_problem(problem)
    if not isinstance(proposal,dict) or set(proposal)!={"empty","step","merge","decode","invariant"}:
        raise SummaryError("Generated summary programs required; no proof/answer flags")
    empty=proposal["empty"]
    if not isinstance(empty,list) or not 1<=len(empty)<=8 or any(type(v)is not int or not -(2**63)<=v<2**63 for v in empty):
        raise SummaryError("Bounded generated empty state required")
    d=len(empty)
    for key,inputs,types in [("step",["head"]+[f"z{i}" for i in range(d)],["Int"]*d),
                             ("merge",[f"l{i}" for i in range(d)]+[f"r{i}" for i in range(d)],["Int"]*d),
                             ("decode",[f"z{i}" for i in range(d)],["Int"]*width),
                             ("invariant",[f"z{i}" for i in range(d)],["Bool"])]:
        validate_program(proposal[key],types)
        if proposal[key]["inputs"] != inputs:
            raise SummaryError("Generated summary ordered interface mismatch")
    return d


def interpret(program,row):
    if len(row)!=len(program["inputs"]) or any(type(v)is not int for v in row):
        raise SummaryError("Exact integer arguments required")
    env=dict(zip(program["inputs"],row))
    def visit(t):
        if type(t)in(int,bool):return t
        if isinstance(t,str):return env[t]
        op=t[0]
        if op=="ite": return visit(t[2]) if visit(t[1]) else visit(t[3])
        if op=="not":return not visit(t[1])
        a,b=visit(t[1]),visit(t[2])
        if op=="add":return a+b
        if op=="sub":return a-b
        if op=="max":return max(a,b)
        if op=="min":return min(a,b)
        if op=="ge":return a>=b
        if op=="le":return a<=b
        if op=="gt":return a>b
        if op=="lt":return a<b
        if op=="eq":return a==b
        if op=="and":return a and b
        if op=="or":return a or b
        raise SummaryError("Invalid validated term")
    return [visit(t) for t in program["outputs"]]


def cvc_program(tm,program,row):
    from cvc5 import Kind
    env=dict(zip(program["inputs"],row))
    kinds={"add":Kind.ADD,"sub":Kind.SUB,"ge":Kind.GEQ,"le":Kind.LEQ,"gt":Kind.GT,"lt":Kind.LT,
           "eq":Kind.EQUAL,"and":Kind.AND,"or":Kind.OR,"not":Kind.NOT,"ite":Kind.ITE}
    def visit(t):
        if type(t)is bool:return tm.mkBoolean(t)
        if type(t)is int:return tm.mkInteger(t)
        if isinstance(t,str):return env[t]
        args=[visit(a) for a in t[1:]]
        if t[0] in {"min","max"}:
            compare=tm.mkTerm(Kind.LEQ if t[0]=="min" else Kind.GEQ,*args)
            return tm.mkTerm(Kind.ITE,compare,*args)
        return tm.mkTerm(kinds[t[0]],*args)
    return [visit(t) for t in program["outputs"]]


def obligations(tm,problem,proposal,merge_override=None,symbol_factory=None):
    from cvc5 import Kind
    d=validate_proposal(problem,proposal)
    variables={}
    def symbol(name):
        variables[name]=(symbol_factory(name) if symbol_factory else tm.mkConst(tm.getIntegerSort(),name))
        return variables[name]
    head=symbol("head")
    z,l,r,a,b,c=[[symbol(f"{prefix}{i}") for i in range(d)] for prefix in ["z","l","r","a","b","c"]]
    empty=[tm.mkInteger(v) for v in proposal["empty"]]
    S=lambda h,x:cvc_program(tm,proposal["step"],[h]+x)
    M=merge_override or (lambda x,y:cvc_program(tm,proposal["merge"],x+y))
    D=lambda x:cvc_program(tm,proposal["decode"],x)
    I=lambda x:cvc_program(tm,proposal["invariant"],x)[0]
    F=lambda h,x:cvc_program(tm,problem["step"],[h]+x)
    AND=lambda *xs:tm.mkTerm(Kind.AND,*xs) if len(xs)>1 else xs[0]
    E=lambda x,y:AND(*[tm.mkTerm(Kind.EQUAL,u,v) for u,v in zip(x,y)])
    IMP=lambda pre,post:tm.mkTerm(Kind.IMPLIES,pre,post)
    rows=[("INITIAL_VALID",I(empty)),("STEP_VALID",IMP(I(z),I(S(head,z)))),
          ("DECODE_EMPTY",E(D(empty),[tm.mkInteger(v) for v in problem["empty"]])),
          ("DECODE_STEP",IMP(I(z),E(D(S(head,z)),F(head,D(z))))),
          ("MERGE_VALID",IMP(AND(I(l),I(r)),I(M(l,r)))),
          ("LEFT_IDENTITY",IMP(I(z),E(M(empty,z),z))),
          ("RIGHT_IDENTITY",IMP(I(z),E(M(z,empty),z))),
          ("CONS_NATURALITY",IMP(AND(I(l),I(r)),E(M(S(head,l),r),S(head,M(l,r))))),
          ("ASSOCIATIVE",IMP(AND(I(a),I(b),I(c)),E(M(M(a,b),c),M(a,M(b,c)))))]
    return rows,variables


def check_summary(problem,proposal,*,timeout_ms=2000,resource_limit=200000):
    import cvc5
    from cvc5 import Kind
    if type(timeout_ms)is not int or not 1<=timeout_ms<=10000 or type(resource_limit)is not int or not 1<=resource_limit<=2000000:
        raise SummaryError("Bounded checker limits required")
    start=perf_counter()
    rows=[]
    try:
        tm=cvc5.TermManager()
        theorems,variables=obligations(tm,problem,proposal)
        declarations="\n".join(f"(declare-fun {name} () Int)" for name in variables)
        for name,theorem in theorems:
            solver=cvc5.Solver(tm)
            solver.setLogic("QF_LIA")
            for key,value in [("produce-models","true"),("tlimit-per",str(timeout_ms)),("rlimit-per",str(resource_limit))]:
                solver.setOption(key,value)
            negation=tm.mkTerm(Kind.NOT,theorem)
            solver.assertFormula(negation)
            result=solver.checkSat()
            row={"obligation":name,"status":str(result),
                 "smt2":"(set-logic QF_LIA)\n"+declarations+"\n(assert "+str(negation)+")\n"}
            if result.isSat():
                row["counterexample"]={key:int(solver.getValue(v).getIntegerValue()) for key,v in variables.items()}
            rows.append(row)
            if not result.isUnsat():break
        accepted=len(rows)==9 and all(r["status"]=="unsat" for r in rows)
        status="CERTIFIED" if accepted else "REFUTED" if any(r["status"]=="sat" for r in rows) else "UNKNOWN"
        error=None
    except (SummaryError,RuntimeError) as exc:
        accepted=False
        status="BAD_PROPOSAL" if isinstance(exc,SummaryError) else "UNKNOWN"
        error=str(exc)
    return {"accepted":accepted,"status":status,"obligations":rows,"error":error,
            "problem_sha256":identity(problem),"proposal_sha256":identity(proposal),
            "solver":"cvc5 "+cvc5.__version__,"verification_seconds":perf_counter()-start,
            "scope":"all finite integer lists via sufficient inductive equations,not arbitrary OCaml programs or learned discovery"}


def reference(problem,values):
    validate_problem(problem)
    if not isinstance(values,list) or len(values)>100000 or any(type(v)is not int for v in values):
        raise SummaryError("Bounded finite exact integer list required")
    state=list(problem["empty"])
    for head in reversed(values):state=interpret(problem["step"],[head]+state)
    return state


class CertifiedSummary:
    def __init__(self,problem,proposal):
        self._problem,self._proposal=deepcopy(problem),deepcopy(proposal)
        self.certificate=check_summary(self._problem,self._proposal)
        if not self.certificate["accepted"]:raise SummaryError("Uncertified summary cannot execute")
        self._binding=(identity(self._problem),identity(self._proposal))

    def run(self,tree,max_nodes=100000):
        if type(max_nodes)is not int or not 1<=max_nodes<=100000:
            raise SummaryError("Bounded tree work required")
        if (identity(self._problem),identity(self._proposal))!=self._binding:
            raise SummaryError("Certificate/program binding changed")
        todo=[(tree,False)]
        states=[]
        visited=0
        p=self._proposal
        while todo:
            node,done=todo.pop()
            if done:
                right,left=states.pop(),states.pop()
                states.append(interpret(p["merge"],left+right))
                continue
            visited+=1
            if visited>max_nodes or not isinstance(node,list) or not node:
                raise SummaryError("Invalid or over-budget constructor tree")
            if node[0]=="nil" and len(node)==1:states.append(list(p["empty"]))
            elif node[0]=="single" and len(node)==2 and type(node[1])is int:
                states.append(interpret(p["step"],[node[1]]+p["empty"]))
            elif node[0]=="concat" and len(node)==3:
                todo.extend([(node,True),(node[2],False),(node[1],False)])
            else:raise SummaryError("Unknown constructor or noninteger payload")
        return interpret(p["decode"],states.pop())
