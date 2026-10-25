"""Proof-aware NEUMANN Q3 observation gate. Classical, not learned invention.
DO NOT promote mere agreement at finite probes to globally CERTIFIED.
"""
from itertools import combinations
from math import comb
UNKNOWN="UNKNOWN_INSUFFICIENT_IDENTIFIABILITY"
CONDITIONAL="COMPLETE_BASIS_CONDITIONAL_ON_VERIFIED_DEGREE_3_MULTILINEAR_GF3"

def required_basis(n,degree=3):
    if degree not in (2,3) or n<3: raise ValueError("unsupported bounded class")
    return frozenset(t for k in range(degree+1) for t in combinations(range(n),k))

def evidence_status(n,observed_binary_supports,max_degree=3):
    """This verifies basis coverage, NOT a proof of target class membership."""
    q=frozenset(tuple(sorted(t)) for t in observed_binary_supports)
    if not required_basis(n,max_degree).issubset(q):return UNKNOWN
    return CONDITIONAL  # explicitly not unconditional CERTIFIED

def cubic_identification_lower_bound(n):
    if n<3:raise ValueError("need at least 3 coordinates")
    return comb(n,3)

def balanced_attacker(x,pairs):
    out=1
    for a,b in pairs:out=out*(x[a]-x[b])%3
    return out

def leave_one_out_catches_two_cubic_terms(n,A,B):
    if len(A)!=3 or len(B)!=3 or set(A)==set(B) or len(set(A))!=3 or len(set(B))!=3:
        raise ValueError("distinct squarefree cubic terms required")
    return any((int(j not in A)-int(j not in B))%3!=0 for j in range(n))

def hidden_unseen_2(x):
    out=1
    for v in x:out=out*(1-(v-2)**2)%3
    return out
