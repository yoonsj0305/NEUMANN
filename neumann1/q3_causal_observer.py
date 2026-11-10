"""Q3 universal lossless causal observer for JSON input/output changes.

The observer has NO ARC/grid/string/graph/number transformation primitives,
NO output predictor, NO learned answer memory, and no task-family branches.
It maps *observed* SOURCE JSON (input, output) to a lossless structural delta
plus the unmodified input. The neural program policy must STILL invent its
own executable transform(x); patches are not replayed on unobserved inputs.

Hypothesis: the old raw-output prompt obscures *what changed*. The
causal edit view makes latent dependencies easier to infer without an
answer-specific operator. It must be empirically ablated on original SOURCE.
"""
from __future__ import annotations

import json


def _equal(a,b):
    return json.dumps(a,sort_keys=True,separators=(",",":"),
                      allow_nan=False,ensure_ascii=True)==json.dumps(
        b,sort_keys=True,separators=(",",":"),
        allow_nan=False,ensure_ascii=True)


def causal_json_edits(before,after):
    """A deterministic finite, lossless observable change set, not a solver."""
    edits=[]
    def walk(a,b,path):
        if _equal(a,b):
            return
        if (type(a) is list and type(b) is list and len(a)==len(b)):
            for index,(x,y) in enumerate(zip(a,b)):
                walk(x,y,(*path,index))
            return
        if (type(a) is dict and type(b) is dict and
                set(a)==set(b)):
            for key in sorted(a):
                walk(a[key],b[key],(*path,key))
            return
        edits.append({"path":list(path),"before":a,"after":b})
    walk(before,after,())
    return tuple(edits)


def replay_observed_edits(before,edits):
    """Independent observer equivalence assertion; no guessing new outputs."""
    clone=json.loads(json.dumps(before,sort_keys=True,allow_nan=False))
    visited=set()
    for e in edits:
        p=e.get("path")
        if not isinstance(p,list):
            raise ValueError("invalid JSON causal path")
        key=json.dumps(p,sort_keys=True)
        if key in visited:
            raise ValueError("duplicated JSON causal edit")
        visited.add(key)
        current=clone
        for part in p[:-1]:
            if type(current) is list:
                if type(part) is not int or not 0<=part<len(current):
                    raise ValueError("invalid JSON index")
                current=current[part]
            elif type(current) is dict:
                if type(part) is not str or part not in current:
                    raise ValueError("invalid JSON map key")
                current=current[part]
            else:
                raise ValueError("invalid JSON path prefix")
        if not p:
            if not _equal(clone,e["before"]):
                raise ValueError("patch before not observed")
            clone=e["after"]
        else:
            last=p[-1]
            if type(current) is list:
                if type(last) is not int or not 0<=last<len(current):
                    raise ValueError("invalid leaf list index")
            elif type(current) is dict:
                if type(last) is not str or last not in current:
                    raise ValueError("invalid leaf map key")
            else:
                raise ValueError("invalid JSON patch leaf")
            if not _equal(current[last],e["before"]):
                raise ValueError("patch before mismatch")
            current[last]=e["after"]
    return clone


def lossless_causal_source_prompt(pairs):
    """Single common-source observer: original input + data-derived edit set.

    Inference receives *training SOURCE only*. Heldout SOURCE and original
    author TARGET remain sealed in the independent checker.
    """
    if not 1<=len(pairs)<=32:
        raise ValueError("bounded observed SOURCE pairs required")
    out=[
        "Infer an executable general causal algorithm from SOURCE changes.",
        "Each SOURCE example shows the complete input and exact observed",
        "changes needed to obtain its output. All paths are zero-based JSON",
        "indices or dictionary keys; [] is whole-value replacement.",
        "Treat the changes as observations, NOT a program to memorize.",
        "Infer the missing latent relations and invariants that explain",
        "changes across examples. Invent ONE self-contained Python",
        "def transform(x) that predicts the full output for a NEW input.",
        "No imports, prewritten solvers, globals, external modules or code",
        "outside the function. Output Python code only.",
    ]
    for x,y in pairs:
        edits=causal_json_edits(x,y)
        # Equivalence is established before the model sees the witness.
        if not _equal(replay_observed_edits(x,edits),y):
            raise ValueError("observer not lossless")
        out.append("Source input: "+json.dumps(
            x,sort_keys=True,ensure_ascii=True,separators=(",",":")))
        out.append("Observed input-to-output edits: "+json.dumps(
            edits,sort_keys=True,ensure_ascii=True,separators=(",",":")))
    return "\n".join(out)
