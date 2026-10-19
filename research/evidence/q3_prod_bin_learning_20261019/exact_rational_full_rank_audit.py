"""Exact rational identifiability replay for post-G0 prod-bin.
Source trajectory arithmetic follows public original branch rules, but ORIGINAL
SMT semantics/certificate authority is the independent GitHub Actions first
Z3+cvc5 receipt; this is an additional pure algebraic finite-data audit.
"""
from __future__ import annotations
import itertools,json
import sympy as sp
TERMS=[t for t in ([()]+[(i,) for i in range(5)]+
  list(itertools.combinations_with_replacement(range(5),2)))
  if t not in {(),(4,),(0,1)}]
assert len(TERMS)==18
def phi(s):
 return [sp.prod(s[i] for i in term) for term in TERMS]
def goal(s):
 a,b,x,y,z=s
 return z-a*b
def trajectories():
 for a,b in itertools.product(range(8),range(11)):
  x,y,z=a,b,0
  seq=[(a,b,x,y,z)]
  while y:
   if y%2==0:x,y=2*x,y//2
   else:y,z=y-1,z+x
   seq.append((a,b,x,y,z))
  yield seq
state=[];steps=[]
for seq in trajectories():
 state.extend(seq)
 steps.extend(zip(seq,seq[1:]))
assert (len(state),len(steps))==(376,288)
X=[];Y=[]
for s in state:
 X.append([int(v) for v in phi(s)]);Y.append(-int(goal(s)))
for s,t in steps:
 old,new=phi(s),phi(t)
 X.append([int(v-u) for u,v in zip(old,new)])
 Y.append(int(goal(s)-goal(t)))
assert (len(X),len(Y))==(664,664)
prime=1000003
basis={};picks=[]
for i,row in enumerate(X):
 v=[u%prime for u in row]
 for idx,pivot in sorted(basis.items()):
  c=v[idx]
  if c:v=[(a-c*b)%prime for a,b in zip(v,pivot)]
 idx=next((j for j,a in enumerate(v) if a),None)
 if idx is None:continue
 inverse=pow(v[idx],-1,prime)
 basis[idx]=[(a*inverse)%prime for a in v]
 picks.append(i)
 if len(picks)==18:break
assert len(picks)==18
M=sp.Matrix([X[i] for i in picks])
minor=int(M.det()%prime)
assert minor!=0
w=M.LUsolve(sp.Matrix([Y[i] for i in picks]))
expected=[sp.Integer(t==(2,3)) for t in TERMS]
assert list(w)==expected
assert all(sum(v*w[k] for k,v in enumerate(row))==b for row,b in zip(X,Y))
print(json.dumps({
 "schema":"neumann.q3.prod-bin.exact-rational-unique-coefficient.audit.v1",
 "rank_over_Q":18,"columns":18,"original_source_steps_recreated":288,
 "rows":664,"minor_nonzero_mod_prime":minor,
 "prime":prime,"independent_rows":picks,
 "unique_coefficients":[int(k) for k in w],
 "unique_active_monomial":[2,3],
 "proof":"determinant mod prime nonzero => integer determinant nonzero => rank full over rational numbers; unique rational solution is x*y coefficient +1.",
 "scientific_limit":"Not a formal universal learned capability impossibility; exact uniqueness only for this frozen finite input matrix and fixed 18-dimensional degree<=2 feature grammar.",
 "global_Q3":"OPEN"},sort_keys=True,indent=2))
