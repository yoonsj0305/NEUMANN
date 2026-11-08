"""Q6 typed-representation transport for Q3-invented Boolean object programs.

A structural selector can act on any collection of entities whose features
are exposed through an explicitly declared mapping. No source task answers
are copied. This proves representation invariance for the shared predicate
algebra, NOT semantic generalization to arbitrary new feature ontologies.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

from .parallel_object_edit_inventor import BulkEditProgram


@dataclass(frozen=True)
class EntityRecord:
    uid: str
    properties: Mapping[str, int]


def apply_learned_selector(program:BulkEditProgram, entities,
                           *,feature_map:Mapping[str,str]):
    """Return IDs selected by an *unchanged* source-invented DNF program.

    Feature mapping is an explicit, auditable interface between domains.
    Relative comparisons are computed over the entire new entity set.
    """
    if not isinstance(program,BulkEditProgram):
        raise TypeError("must reuse original Q3 executable AST")
    entities=tuple(entities)
    if not entities:return ()
    required={atom[1] for clause in program.clauses for atom in clause}
    if not required.issubset(feature_map):
        raise ValueError("missing typed domain feature interface")
    if len({e.uid for e in entities})!=len(entities):
        raise ValueError("duplicate entity IDs")
    vals={}
    for feature in required:
        key=feature_map[feature]
        numbers=[]
        for e in entities:
            if key not in e.properties or type(e.properties[key]) is not int:
                raise ValueError("invalid typed feature")
            numbers.append(e.properties[key])
        vals[feature]=tuple(numbers)
    selected=[]
    for i,e in enumerate(entities):
        def evaluate(atom):
            kind,feature,threshold=atom
            value=vals[feature][i]
            if kind=="relative":
                v=vals[feature]
                if threshold=="min":return value==min(v)
                if threshold=="max":return value==max(v)
                if threshold=="lt_max":return value<max(v)
                if threshold=="gt_min":return value>min(v)
                raise ValueError("unknown relational primitive")
            if kind=="exact":return value==threshold
            if kind=="upper":return value<=threshold
            if kind=="lower":return value>=threshold
            raise ValueError("unknown comparison primitive")
        if any(all(evaluate(atom) for atom in clause)
               for clause in program.clauses):
            selected.append(e.uid)
    return tuple(selected)
