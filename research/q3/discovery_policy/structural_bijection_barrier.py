"""Fail-closed structural impossibility gate for the legacy 8-bit A/X/R DSL.

A theorem relative to the DECLARED grammar, not a theorem about all
classical algorithms, arbitrary neural systems or general intelligence.
"""
from typing import Callable

BYTE_MAX = 255
PROVEN_BIJECTIVE_CLASSES = frozenset(("A", "X", "R"))

def test_structural_representation_barrier(
    original_function: Callable[[int], int],
    admitted_operator_classes: tuple[str, ...],
    witness: tuple[int, int] | None = None,
) -> dict:
    """Prove impossible in ANY-LENGTH composition of byte ADD/XOR/ROL.

    Primitive invertibility has algebraic proof: additive inverse,
    XOR involution, inverse right rotation. Thus any finite composition
    is injective. Exhibit two distinct inputs mapping to the same output.
    This certificate says nothing about an augmented grammar with shifts.
    """
    if any(op not in PROVEN_BIJECTIVE_CLASSES for op in admitted_operator_classes):
        return {
            "status": "UNKNOWN_GRAMMAR_HAS_UNPROVEN_OPERATOR",
            "automatically_promote_Q": False,
        }
    if witness is not None:
        if len(witness) != 2:
            return {"status": "HOLD_INVALID_WITNESS", "automatically_promote_Q": False}
        pairs = (witness,)
    else:
        pairs = None

    def evaluate_byte(x: int):
        y=original_function(x)
        if type(y) is not int or not (0 <= y <= BYTE_MAX):
            raise ValueError("Outside 8-bit total function")
        return y

    try:
        if pairs is not None:
            x1,x2=pairs[0]
            if type(x1) is not int or type(x2) is not int or not (
                0<=x1<=BYTE_MAX and 0<=x2<=BYTE_MAX and x1!=x2
            ):
                return {"status":"HOLD_INVALID_WITNESS","automatically_promote_Q":False}
            y1,y2=evaluate_byte(x1),evaluate_byte(x2)
            if y1!=y2:
                return {"status":"HOLD_INVALID_WITNESS","automatically_promote_Q":False}
        else:
            first_seen={}
            x1=x2=y1=None
            for x in range(256):
                y=evaluate_byte(x)
                if y in first_seen:
                    x1=first_seen[y]
                    x2=x
                    y1=y
                    break
                first_seen[y]=x
    except Exception:
        return {"status":"HOLD_INVALID_FUNCTION_OR_EXECUTION","automatically_promote_Q":False}
    if x1 is None:
        return {
            "status":"NO_INJECTIVITY_EXCLUSION_FOUND",
            "checked_all_256_inputs":True,
            "automatically_promote_Q":False,
        }
    return {
        "status":"PROVEN_UNREPRESENTABLE_IN_DECLARED_BIJECTIVE_DSL",
        "proof_scope":"Any finite sequence of 8-bit ADD(c), XOR(c), ROL(r), with all legal parameters",
        "proof_rule":"Composition of bijections is a bijection; distinct-input collision contradicts injectivity",
        "distinct_input_witness": [x1,x2],
        "equal_output":y1,
        "witness_evaluations":2 if witness is not None else x2+1,
        "automatically_promote_Q":False,
    }
