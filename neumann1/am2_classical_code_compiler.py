"""Strict bounded public-spec compiler for AM2 opened-source baseline ceiling.
Compiler reads ONLY the task's model-visible natural-language requirement.
It does not read original checker private tests, task ID, family or hidden answers.
This is a transparent classical NEW TOOL CHALLENGER, not frozen AM1 TOOL.
Preregistered GitHub Issue #249 before any original CPU run.
"""
from __future__ import annotations
import hashlib
import re

PATTERN=re.compile(
 r"^Return the (?P<agg>number|sum)(?P<abs> of absolute values)?"
 r" of distinct (?P<mods>(?:(?:positive|negative|nonzero|even|odd) )+)"
 r"integers in items, a list of integers\.$"
)
ALLOWED_MODS={"positive","negative","nonzero","even","odd"}


class UnsupportedSpec(ValueError):
    pass


def compile_public_requirement(requirement):
    """No eval, fuzzy matching, task ID, hidden labels, or per-case string matching."""
    if type(requirement) is not str or len(requirement)>320:
        raise UnsupportedSpec("SOURCE_NOT_SHORT_PUBLIC_TEXT")
    m=PATTERN.fullmatch(requirement)
    if m is None:
        raise UnsupportedSpec("UNSUPPORTED_PUBLIC_SPEC_GRAMMAR")
    mods=m["mods"].split()
    flags=set(mods)
    if len(flags)!=len(mods) or not flags<=ALLOWED_MODS:
        raise UnsupportedSpec("DUPLICATE_OR_UNSUPPORTED_MODIFIERS")
    if ("positive" in flags and "negative" in flags
        or "even" in flags and "odd" in flags
        or "nonzero" in flags and ("positive" in flags or "negative" in flags)):
        raise UnsupportedSpec("CONTRADICTORY_OR_REDUNDANT_MODIFIERS")
    aggregate=m["agg"]
    absolute=m["abs"] is not None
    if aggregate=="number" and absolute:
        raise UnsupportedSpec("ABSOLUTE_CARDINALITY_NOT_IN_GRAMMAR")
    conditions=[]
    for mod in sorted(flags):
        conditions.append({
            "negative":"n < 0",
            "positive":"n > 0",
            "nonzero":"n != 0",
            "even":"n % 2 == 0",
            "odd":"n % 2 != 0",
        }[mod])
    predicate=" and ".join(conditions) if conditions else "True"
    if aggregate=="number":
        result="len([n for n in set(items) if "+predicate+"])"
    else:
        elem="abs(n)" if absolute else "n"
        result="sum("+elem+" for n in set(items) if "+predicate+")"
    source="def solve(items):\n    return "+result
    return {"source":source,
        "public_requirement_sha256":hashlib.sha256(requirement.encode()).hexdigest(),
        "grammar":"distinct-integer-filter-and-aggregate-v1",
        "operator_tokens":{"aggregation":aggregate,"absolute":absolute,
                           "modifiers":sorted(flags)},
        "learned_model_calls":0,
    }
