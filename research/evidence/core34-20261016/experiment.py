"""CORE-34 development-only matched candidate-space audit.

Synthetic integer/list recurrence. Not a neural or external CHC test.
Requires sympy. Run: python experiment.py --output receipt.json
"""
from __future__ import annotations

import argparse
import itertools
import json
from fractions import Fraction
from pathlib import Path
from time import perf_counter_ns

import sympy as sp

A_VALUES = tuple(range(-4, 5))
B_VALUES = tuple(range(-4, 5))
C_VALUES = tuple(range(-4, 5))
D_VALUES = tuple(range(-2, 3))
PROBES = ((0, (), ()), (1, (), ()), (0, (1,), ()), (0, (), (1,)))
VARS = sp.symbols("z sb ft h")


def fold(z, seq, nil_offset=0):
    # Source recurrence: F(z,nil)=z+offset;
    # F(z,cons(h,t))=h+F(z,t)
    if not seq:
        return z + nil_offset
    return seq[0] + fold(z, seq[1:], nil_offset)


def candidate_rhs(p, z, aa, bb, offset=0):
    a, b, c, d = p
    return a * fold(z, aa, offset) + b * fold(0, bb, offset) + c*z + d


def observes(p, offset=0):
    return all(fold(z, aa+bb, offset) == candidate_rhs(p, z, aa, bb, offset)
               for z, aa, bb in PROBES)


def proof(p, offset=0):
    """Exact universal structural induction for a fully typed candidate.

    Base checks A=nil for all z,B. Step checks A=cons(h,t) using
    candidate as induction hypothesis. Nonzero polynomials are rejected.
    """
    a, b, c, d = p
    z, sb, ft, h = VARS
    # sb=F(0,B); F(z,B)=z+sb for this source.
    base_lhs = z + offset + (sb-offset)
    base_rhs = a*(z+offset) + b*sb + c*z + d
    base_diff = sp.Poly(sp.expand(base_lhs-base_rhs), z, sb)
    step_lhs_via_ih = h + (a*ft + b*sb + c*z + d)
    step_rhs = a*(h+ft) + b*sb + c*z + d
    step_diff = sp.Poly(sp.expand(step_lhs_via_ih-step_rhs), z, sb, ft, h)
    return base_diff.is_zero and step_diff.is_zero


def proof_explicit(p, offset=0):
    """Independent coefficient identity derived from recurrence."""
    a, b, c, d = p
    closed = (a == 1 and b == 1 and a+c == 1 and
              (a+b)*offset+d == offset)
    return closed, proof(p, offset)


def rank_of_matrix(rows):
    if not rows:
        return 0
    mat = [r[:] for r in rows]
    piv = 0
    n = len(mat[0])
    for j in range(n):
        ix = next((i for i in range(piv, len(mat)) if mat[i][j]), None)
        if ix is None:
            continue
        mat[piv], mat[ix] = mat[ix], mat[piv]
        k = mat[piv][j]
        mat[piv] = [v/k for v in mat[piv]]
        for i in range(len(mat)):
            if i != piv:
                f = mat[i][j]
                mat[i] = [x-f*y for x, y in zip(mat[i], mat[piv])]
        piv += 1
        if piv == len(mat):
            break
    return piv


def direct_solve(offset=0):
    """Strong classical baseline: four source probes, exact linear solve."""
    rows = []
    for z, aa, bb in PROBES:
        rows.append([Fraction(fold(z, aa, offset)),
                     Fraction(fold(0, bb, offset)),
                     Fraction(z), Fraction(1),
                     Fraction(fold(z, aa+bb, offset))])
    assert rank_of_matrix([r[:4] for r in rows]) == 4
    aug = [r[:] for r in rows]
    for col in range(4):
        p = next(i for i in range(col, 4) if aug[i][col])
        aug[col], aug[p] = aug[p], aug[col]
        scale = aug[col][col]
        aug[col] = [v/scale for v in aug[col]]
        for i in range(4):
            if i != col:
                f = aug[i][col]
                aug[i] = [x-f*y for x, y in zip(aug[i], aug[col])]
    out = tuple(int(aug[i][-1]) for i in range(4))
    assert all(Fraction(v) == aug[i][-1] for i,v in enumerate(out))
    return out


def generate():
    return itertools.product(A_VALUES, B_VALUES, C_VALUES, D_VALUES)


def run():
    count = len(A_VALUES)*len(B_VALUES)*len(C_VALUES)*len(D_VALUES)
    start = perf_counter_ns()
    exhaustive = [p for p in generate() if proof(p)]
    exhaustive_ns = perf_counter_ns()-start
    start = perf_counter_ns()
    filtered = [p for p in generate() if observes(p)]
    filtered_ns = perf_counter_ns()-start
    start = perf_counter_ns()
    admitted = [p for p in filtered if proof(p)]
    admitted_ns = perf_counter_ns()-start
    start = perf_counter_ns()
    strong = direct_solve()
    strong_cert = proof(strong)
    strong_ns = perf_counter_ns()-start
    assert exhaustive == filtered == admitted == [strong] == [(1,1,0,0)]
    assert strong_cert and proof_explicit(strong) == (True,True)
    # Poisoned source must reject the original (now false) lemma.
    assert not proof(strong, offset=1)
    assert not observes(strong, offset=1)
    assert not proof((0,1,1,0))
    return {
        "experiment":"CORE-34",
        "status":"RESTRICTED_CLASSICAL_MATCHED_SPACE_VERIFIED",
        "global_Q1_Q7":"OPEN",
        "synthetic":True, "neural_forwards":0,
        "candidate_count":count,
        "grammar":"a*F(z,A)+b*F(0,B)+c*z+d",
        "coefficient_domains":{"a":list(A_VALUES),"b":list(B_VALUES),
                               "c":list(C_VALUES),"d":list(D_VALUES)},
        "probe_count":len(PROBES),
        "probe_spec":[{"z":z,"A":aa,"B":bb} for z,aa,bb in PROBES],
        "exhaustive_verified_count":count,
        "exhaustive_valid":exhaustive,
        "selective_probe_survivors":len(filtered),
        "selective_universal_proofs":len(filtered),
        "direct_solved":strong, "universally_certified":True,
        "negative_controls":{"nil_base_mutation_rejected":True,
                             "wrong_constructor_coefficient_rejected":True},
        "wall_ns":{"exhaustive_proofs":exhaustive_ns,
                   "probe_filter":filtered_ns,
                   "selective_proofs":admitted_ns,
                   "selective_total":filtered_ns+admitted_ns,
                   "direct_linear_solve_plus_proof":strong_ns},
        "speedup_exhaustive_over_selective":round(
             exhaustive_ns/(filtered_ns+admitted_ns),3),
        "speedup_exhaustive_over_strong_direct":round(exhaustive_ns/strong_ns,3),
        "sympy_version":sp.__version__,
        "inference_or_training_cost":"none",
        "scientific_limit":"Synthetic linear additive list/fold source; exact "
        "algebraic direct baseline is available. No learned invention, "
        "no authentic CHC transfer, no frontier/Q closure."
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    result=run()
    content=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.output:
        args.output.write_text(content,encoding="utf-8")
    print(content)


if __name__=="__main__":
    main()
