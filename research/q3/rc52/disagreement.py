"""RC52 generic independent disagreement auditor.

This module has NO solver, test labels, pretrained model, or hidden oracle.
It CANNOT tell which source-consistent hypothesis is correct. Scope: bounded
finite ARC-style grid predictions. Full historical retrospective witness
on ARC-AGI-2 351d6448 in conversation RC52 ZIP.
"""
from __future__ import annotations
from math import ceil, log2

def _shape(pred):
    if not isinstance(pred,list) or not pred or not isinstance(pred[0],list) or not pred[0]:
        raise ValueError("nonempty grid required")
    h,w=len(pred),len(pred[0])
    if any(not isinstance(row,list) or len(row)!=w for row in pred):
        raise ValueError("ragged grid")
    if any(type(x)!=int or not 0<=x<=9 for row in pred for x in row):
        raise ValueError("ARC bounded integer colors")
    return h,w

def audit_predictions(source_compatible: dict):
    """Input: name -> independently source-verified candidate output grid.
    Never turns SOURCE_FIT into true-task proof or auto authorizes neural.
    Unknown/shape violations -> fail closed.
    """
    if not source_compatible:
        return {"status":"HOLD_NO_SOURCE_CANDIDATES","neural_authorized":False}
    shapes=[]
    try:
        for grid in source_compatible.values():shapes.append(_shape(grid))
    except (ValueError,TypeError):
        return {"status":"HOLD_INVALID_PREDICTIONS","neural_authorized":False}
    if len(set(shapes))!=1:
        return {"status":"HOLD_SHAPE_DISAGREEMENT","neural_authorized":False}
    h,w=shapes[0];preds=list(source_compatible.values())
    disputed=[{"row":i,"col":j,"possible_values":sorted({g[i][j] for g in preds})}
              for i in range(h) for j in range(w)
              if len({g[i][j] for g in preds})>1]
    distinct=len({str(g) for g in preds})
    return {
        "status":"HOLD_SEMANTIC_AMBIGUITY" if disputed else "SOURCE_CONSENSUS_ONLY",
        "disagreement_cells":disputed,
        "hypothesis_count":len(preds),
        "distinct_outputs":distinct,
        "candidate_identity_bits_ceiling":ceil(log2(distinct)) if distinct>1 else 0,
        "confident_result":None if disputed else preds[0],
        "neural_authorized":False,
        "global_questions_closed":[],
    }
