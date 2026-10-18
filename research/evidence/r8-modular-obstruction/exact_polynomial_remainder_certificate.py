"""R8 generic sound finite modular obstruction checker (development + body-unseen holdout).

Algorithm preregistration: https://github.com/yoonsj0305/NEUMANN/issues/231
NO original source name/constant/class hardcoded. NO neural. Theorem: original necessary
integer polynomial equality E=F is UNSAT if some m>=2 has ZERO absent among
the exact residues of E-F for ALL integer-variable residue assignments modulo m.
Each accepted certificate is independently checked by a second SymPy ZZ-polynomial
evaluator against the same COMPLETE original necessary SMT-LIB equality.
"""
import hashlib,itertools,json,sys,time
from pathlib import Path
import sympy as sp
import z3

MAX_VARIABLES=4
MAX_MOD=12
MAX_ASSIGNMENTS=50000
MAX_AST_DEPTH=120

class Unsupported(Exception):pass

def required_atoms():
 raise RuntimeError("Use original source parser in main(path)")

def necessary(expr):
 if z3.is_and(expr):
  for x in expr.children():
   yield from necessary(x)
 else:
  yield expr

def symbol_if_any(expr):
 if (z3.is_const(expr) and expr.num_args()==0 and z3.is_int(expr) and
     expr.decl().kind()==z3.Z3_OP_UNINTERPRETED):
  return expr.decl().name()
 return None

def tree(expr,depth=0):
 if depth>MAX_AST_DEPTH:raise Unsupported("AST_DEPTH")
 if z3.is_int_value(expr):return ("int",expr.as_long())
 sym=symbol_if_any(expr)
 if sym is not None:return ("var",sym)
 typ=expr.decl().kind()
 if typ==z3.Z3_OP_POWER:
  if len(expr.children())!=2 or not z3.is_int_value(expr.arg(1)):
   raise Unsupported("NON_CONSTANT_POWER")
  p=expr.arg(1).as_long()
  if p<0 or p>16:raise Unsupported("POWER_OUT_OF_SUPPORTED_RANGE")
  return ("pow",tree(expr.arg(0),depth+1),p)
 args=tuple(tree(x,depth+1) for x in expr.children())
 if typ==z3.Z3_OP_ADD:return ("add",)+args
 if typ==z3.Z3_OP_MUL:return ("mul",)+args
 if typ==z3.Z3_OP_SUB:return ("sub",)+args
 if typ==z3.Z3_OP_UMINUS:return ("neg",)+args
 raise Unsupported("EXPRESSION_NOT_INTEGER_POLYNOMIAL")

def variables(node):
 if node[0]=="var":return {node[1]}
 if node[0] in ("int",):return set()
 if node[0]=="pow":return variables(node[1])
 s=set()
 for item in node[1:]:
  if isinstance(item,tuple):s.update(variables(item))
 return s

def modular_eval(node,assign,m):
 typ=node[0]
 if typ=="int":return node[1]%m
 if typ=="var":return assign[node[1]]%m
 if typ=="add":return sum(modular_eval(x,assign,m) for x in node[1:])%m
 if typ=="mul":
  value=1
  for x in node[1:]:value=(value*modular_eval(x,assign,m))%m
  return value
 if typ=="sub":
  if len(node)<2:raise Unsupported("MALFORMED_SUBTRACTION")
  return (modular_eval(node[1],assign,m)-
         sum(modular_eval(x,assign,m) for x in node[2:]))%m
 if typ=="neg":return (-modular_eval(node[1],assign,m))%m
 if typ=="pow":return pow(modular_eval(node[1],assign,m),node[2],m)
 raise Unsupported("MOD_EVAL_NODE")

def symbolic(expr,depth=0):
 """Second independently authored interpreter from original Z3 AST into SymPy ZZ."""
 if depth>MAX_AST_DEPTH:raise Unsupported("INDEPENDENT_AST_DEPTH")
 if z3.is_int_value(expr):return sp.Integer(expr.as_long())
 v=symbol_if_any(expr)
 if v is not None:return sp.Symbol(v,integer=True)
 k=expr.decl().kind()
 if k==z3.Z3_OP_POWER:
  if not z3.is_int_value(expr.arg(1)):raise Unsupported("INDEPENDENT_POWER")
  exponent=expr.arg(1).as_long()
  if exponent<0 or exponent>16:raise Unsupported("INDEPENDENT_POWER_BOUND")
  return symbolic(expr.arg(0),depth+1)**exponent
 args=[symbolic(x,depth+1) for x in expr.children()]
 if k==z3.Z3_OP_ADD:return sp.Add(*args)
 if k==z3.Z3_OP_MUL:return sp.Mul(*args)
 if k==z3.Z3_OP_SUB:return args[0]-sum(args[1:])
 if k==z3.Z3_OP_UMINUS:return -args[0]
 raise Unsupported("INDEPENDENT_NOT_ZZ_POLYNOMIAL")

def independent_verify(lhs,rhs,m,names,expected_residues):
 expr=sp.expand(symbolic(lhs)-symbolic(rhs))
 names2=sorted(str(s) for s in expr.free_symbols)
 if names2!=names:raise Unsupported("INDEPENDENT_SYMBOLS_DIFFER")
 if not names:
  residues={int(expr)%m}
 else:
  vars_=[sp.Symbol(name,integer=True) for name in names]
  p=sp.Poly(expr,*vars_,domain=sp.ZZ)
  residues=set()
  for v in itertools.product(range(m),repeat=len(names)):
   residues.add(int(p.eval(dict(zip(vars_,v))))%m)
 if residues!=expected_residues:raise RuntimeError("DUAL_REMAINDER_CERTIFIER_DISAGREES")
 if 0 in residues:raise RuntimeError("FALSE_MODULAR_OBSTRUCTION")
 return {"verifier":"independent_sympy_polynomial_ZZ_full_residue_replay",
         "polynomial_difference":str(expr),"reachable_residues":sorted(residues),
         "modulus":m,"assignments_checked":m**len(names),"zero_excluded":True}

def prove(path):
 started=time.perf_counter()
 original=Path(path).read_bytes()
 solver=z3.Solver()
 solver.from_file(str(path))
 required=[p for a in solver.assertions() for p in necessary(a)]
 targets=0;unsupported=0;total_attempts=0
 for a in required:
  if not z3.is_eq(a):continue
  lhs,rhs=a.children()
  if not (z3.is_int(lhs) and z3.is_int(rhs)):continue
  targets+=1
  try:
   left,right=tree(lhs),tree(rhs)
   varnames=sorted(variables(left)|variables(right))
   if len(varnames)>MAX_VARIABLES:
    unsupported+=1;continue
   for m in range(2,MAX_MOD+1):
    states=m**len(varnames)
    if states>MAX_ASSIGNMENTS:continue
    residues=set()
    for values in itertools.product(range(m),repeat=len(varnames)):
     total_attempts+=1
     mapping=dict(zip(varnames,values))
     diff=(modular_eval(left,mapping,m)-modular_eval(right,mapping,m))%m
     residues.add(diff)
     if diff==0:break
    if 0 in residues:continue
    if len(residues)==0 or total_attempts<=0:raise RuntimeError("NO_ENUMERATION")
    independently=independent_verify(lhs,rhs,m,varnames,residues)
    return {"status":"INDEPENDENT_ORIGINAL_UNSAT_MODULAR_CERTIFICATE",
      "method":"exhaustive_exact_modular_residue_obstruction",
      "source_sha256":hashlib.sha256(original).hexdigest(),
      "original_assertion_count":len(solver.assertions()),
      "necessary_atom_sexpr":a.sexpr(),"necessary_equalities_examined":targets,
      "integer_source_variables":varnames,"modulus":m,
      "reachable_difference_residues":sorted(residues),
      "enumerated_residue_assignments":states,
      "zero_residue_impossible":True,
      "independent_verifier":independently,
      "no_original_constraint_removed_or_invented":True,
      "wall_s":round(time.perf_counter()-started,6)}
  except (Unsupported,sp.PolynomialError) as error:
   unsupported+=1
   continue
 return {"status":"NO_SOUNDED_MODULAR_CERTIFICATE","source_sha256":hashlib.sha256(original).hexdigest(),
   "original_assertion_count":len(solver.assertions()),
   "necessary_equalities_examined":targets,"unsupported_equalities":unsupported,
   "evaluations_attempted":total_attempts,
   "wall_s":round(time.perf_counter()-started,6)}

if __name__=="__main__":
 try:
  print(json.dumps(prove(sys.argv[1]),sort_keys=True),flush=True)
 except Exception as e:
  print(json.dumps({"status":"PROOF_EXECUTION_ERROR","error_type":type(e).__name__,
   "error":str(e)[:250]}),flush=True)
  sys.exit(1)
