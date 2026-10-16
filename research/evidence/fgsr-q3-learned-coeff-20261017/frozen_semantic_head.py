"""Human-reviewable inference from actually trained 27 neural parameters.

The only input is two extracted three-Int affine transition increments.
Neural matrix entries live in FROZEN_TRAINED_WEIGHTS.json. This simple source
family is fully solved faster by classical cross product; do not claim Q3.
Full original SMT-LIB AST reader, verifier and test receipts are in the
reproducible conversation artifact NEUMANN1_LEARNED_SEMANTIC_P0_20261017.zip.
"""
from __future__ import annotations
import json
import math
from pathlib import Path

PATH=Path(__file__).with_name("FROZEN_TRAINED_WEIGHTS.json")

def numeric_invariant(u: tuple[int,int,int], v: tuple[int,int,int]):
    if len(u)!=3 or len(v)!=3 or not all(type(x) is int for x in (*u,*v)):
        raise ValueError("Only authenticated three-Int affine increment vectors accepted")
    W=json.loads(PATH.read_text(encoding="utf-8"))["trained_weight_matrix"]
    if len(W)!=3 or any(len(row)!=9 for row in W):
        raise ValueError("Frozen learned shape invalid")
    x=[a*b for a in u for b in v]
    generated=[round(sum(a*b for a,b in zip(row,x))) for row in W]
    d=math.gcd(*[abs(int(a)) for a in generated])
    if not d:raise ValueError("Trained model returned no nontrivial semantic relation")
    generated=tuple(int(a)//d for a in generated)
    # No exact symbolic cross-product recovery, coefficient replacement or repair.
    return {
        "learned_coefficients":generated,
        "typed_semantic_relation":
            "(= (+ " + " ".join(f"(* {a} {name})" for a,name in zip(
                generated,("x","y","z"))) + ") 0)",
        "not_independently_proven_here":True,
        "global_q1_q7":"OPEN"
    }

if __name__=="__main__":
    # A displayed example is NOT a blinded test or source-level proof.
    print(numeric_invariant((1,2,3),(2,0,1)))
