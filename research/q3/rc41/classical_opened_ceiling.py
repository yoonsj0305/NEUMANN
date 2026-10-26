"""Post-hoc RC41 opened-task classical capability ceiling.
NOT a frozen AM1 direct/tool/neumann arm, not an independently blind benchmark.
Only model-visible instruction and public inputs enter this route.
"""
import ast,itertools,re
from fractions import Fraction

GRAMMAR=re.compile(
  r"^Return the (?P<aggregation>number|sum|sum of absolute values) of distinct "
  r"(?P<predicate>negative|even|positive odd|nonzero) integers in items, "
  r"a list of integers\.$")
PRED={
 "negative":"x < 0","even":"x % 2 == 0",
 "positive odd":"x > 0 and x % 2 != 0","nonzero":"x != 0",
}

def compile_code(requirement):
    if type(requirement)!=str:return None
    m=GRAMMAR.fullmatch(requirement)
    if m is None:return None
    pred=PRED[m['predicate']]
    if m['aggregation']=="number":f=f"len(set(x for x in items if {pred}))"
    elif m['aggregation']=="sum":f=f"sum(set(x for x in items if {pred}))"
    else:f=f"sum(abs(x) for x in set(items) if {pred})"
    return "def solve(items):\n    return "+f+"\n"

def fraction(expr,bindings):
    tree=ast.parse(expr,mode='eval')
    if len(list(ast.walk(tree)))>256:raise ValueError("AST budget")
    def visit(n):
        if isinstance(n,ast.Constant) and type(n.value)==int:return Fraction(n.value)
        if isinstance(n,ast.Name):
            if n.id not in bindings or type(bindings[n.id])!=int:raise ValueError("bindings")
            return Fraction(bindings[n.id])
        if isinstance(n,ast.BinOp):
            a,b=visit(n.left),visit(n.right)
            if isinstance(n.op,ast.Add):return a+b
            if isinstance(n.op,ast.Sub):return a-b
            if isinstance(n.op,ast.Mult):return a*b
            if isinstance(n.op,ast.Div):return a/b
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):
            v=visit(n.operand)
            return v if isinstance(n.op,ast.UAdd) else -v
        raise ValueError("unsupported expression")
    return str(visit(tree.body))

def consistent(assignment,constraints):
    for op,x,y in constraints:
        if x not in assignment or (type(y)==str and y not in assignment):continue
        a,b=assignment[x],assignment[y] if type(y)==str else y
        if op=="lt" and not a<b:return False
        if op=="le" and not a<=b:return False
        if op=="eq" and not a==b:return False
        if op=="ne" and not a!=b:return False
        if op not in ("lt","le","eq","ne"):raise ValueError("operator")
    return True

def solve_csp(domains,constraints):
    if len(domains)>9 or any(type(v)!=list or len(v)>8 for v in domains.values()):
        raise ValueError("bounded CSP")
    def search(a):
        if len(a)==len(domains):return dict(a)
        plan=[]
        for k in sorted(set(domains)-set(a)):
            allowed=[v for v in domains[k] if consistent({**a,k:v},constraints)]
            plan.append((len(allowed),k,allowed))
        _,key,allowed=min(plan)
        for val in allowed:
            outcome=search({**a,key:val})
            if outcome is not None:return outcome
        return None
    return search({})

def solve_public_view(view):
    if type(view)!=dict or set(view)!=set(("instruction","public")):raise ValueError("public only")
    p=view["public"]
    if type(p)!=dict:raise ValueError("public")
    if "expression" in p and "bindings" in p:
        return {"status":"CANDIDATE","route":"exact_fraction","answer":fraction(p["expression"],p["bindings"])}
    if "requirement" in p:
        answer=compile_code(p["requirement"])
        return {"status":"CANDIDATE" if answer is not None else "UNKNOWN",
                "route":"safe_program_grammar","answer":answer}
    if "domains" in p and "constraints" in p:
        return {"status":"CANDIDATE","route":"classical_mrv",
                "answer":solve_csp(p["domains"],p["constraints"])}
    return {"status":"UNKNOWN_UNSUPPORTED_PUBLIC_SHAPE","route":None,"answer":None}
