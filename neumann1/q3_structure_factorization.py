"""Task-agnostic compression of nested SOURCE transformations.

This is a REPRESENTATION PROPOSAL layer for the one Q3 discovery policy.
Input and output examples are treated as generic JSON trees with indexed
children, never as an "ARC task", "physics task", or a named benchmark.

The system induces a lower-description-length operation from what stays
constant across SOURCE examples: a leaf relation, a coordinate permutation,
or a translated sparse set of equal-valued elements. Each successful factor
is compiled to an ordinary sandbox-valid Python `transform(x)` program.
Every candidate MUST go through the existing independent SOURCE verifier.
No original TARGET outputs are read; no hand-written per-task solutions.

A factored transform is not a newly invented operation *grammar*. Demonstrate
learned policy advantage over the same unlearned language before global Q3.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from typing import Any

from .open_program_inventor import source_same_value, validate_code


@dataclass(frozen=True)
class StructuralFactor:
    program: str
    representation: str
    description_length: int
    source_examples: int


def _kind(v: Any):
    if type(v) in (int, float, bool, str, type(None)):
        return type(v).__name__
    if type(v) is list:
        return "list"
    return "unsupported"


def _leaves(a, b):
    """Yield paired leaves IFF BOTH structures share the exact same tree."""
    if type(a) is list and type(b) is list and len(a)==len(b):
        result=[]
        for av,bv in zip(a,b):
            pairs=_leaves(av,bv)
            if pairs is None:return None
            result.extend(pairs)
        return result
    if type(a) is list or type(b) is list:
        return None
    if _kind(a)=="unsupported" or _kind(b)=="unsupported":
        return None
    return [(a,b)]


def _all_leaves(source_pairs):
    data=[]
    for x,y in source_pairs:
        paired=_leaves(x,y)
        if paired is None:return None
        data.extend(paired)
    return data


def _propose_leaf_relationship(source_pairs):
    pairs=_all_leaves(source_pairs)
    if not pairs or len(pairs)>3000:
        return []
    # Constant-output and identity witnesses are deliberately not asserted
    # as causal rules; they are still valid development hypotheses.
    candidates=[]
    if all(source_same_value(a,b) for a,b in pairs):
        candidates.append(("identity","return x",2))
    if all(type(a) is int and type(b) is int for a,b in pairs):
        delta={b-a for a,b in pairs}
        if len(delta)==1 and next(iter(delta))!=0:
            d=next(iter(delta))
            if abs(d)<=1000000:
                candidates.append(
                    ("leaf-affine-add",f"return v + ({d})",6))
        if all(a!=0 for a,b in pairs):
            # Preserve integer semantics, reject float/non-integral division.
            factors={b//a for a,b in pairs if b%a==0}
            if len(factors)==1 and all(
                    b==a*next(iter(factors)) for a,b in pairs):
                factor=next(iter(factors))
                if factor not in (0,1) and abs(factor)<=1000000:
                    candidates.append(
                        ("leaf-affine-multiply",
                         f"return v * ({factor})",7))
    # Infer a finite-valued *relation*, not position-indexed answer cache.
    if all(type(a) in (int,str) and type(b) in (int,str)
           for a,b in pairs):
        mapping={}
        consistent=True
        for a,b in pairs:
            key=(type(a).__name__,a)
            if key in mapping and not source_same_value(mapping[key],b):
                consistent=False
                break
            mapping[key]=b
        if consistent and len(mapping)<=14:
            # Do not emit a target-answer table for every distinct source
            # cell. Allow categorical maps only when inputs actually repeat,
            # and when every input category occurs in multiple locations.
            counts=Counter((type(a).__name__,a) for a,b in pairs)
            if counts and all(n>=2 for n in counts.values()):
                code="{"+",".join(
                    f"{repr(key[1])}: {repr(value)}"
                    for key,value in sorted(mapping.items(),
                                            key=lambda pair:repr(pair[0]))
                    )+"}"
                candidates.append((
                    "leaf-category-relation",
                    "return "+code+".get(v,v)",5+2*len(mapping)))
    out=[]
    for representation,body,dl in candidates:
        if body=="return x":
            program="def transform(x):\n    return x"
        else:
            program=(
                "def transform(x):\n"
                "    def factor(v):\n"
                "        if isinstance(v,list):\n"
                "            return [factor(t) for t in v]\n"
                f"        {body}\n"
                "    return factor(x)"
            )
        out.append(StructuralFactor(
            validate_code(program),representation,dl,len(source_pairs)))
    return out


def _shape(v):
    if type(v) is not list:
        return ()
    if not v:
        return (0,)
    sub=[_shape(x) for x in v]
    if len(set(sub))!=1:return None
    return (len(v),)+sub[0]


def _same_shape_sources(source_pairs, dimension):
    shapes=[_shape(x) for x,y in source_pairs]
    return bool(shapes and all(
        shape is not None and len(shape)==dimension and
        shape==_shape(y)
        for shape,(x,y) in zip(shapes,source_pairs)))


def _flat(v):
    if type(v) is list:
        for child in v:
            yield from _flat(child)
    else:
        yield v


def _symbol_mode(v):
    data=list(_flat(v))
    if not data or any(type(t) not in (int,str,bool)
                       for t in data):
        return None
    return Counter(data).most_common(1)[0][0]


def _flip_transform(v,axis):
    if axis=="reverse-outer":
        return list(reversed(v))
    if axis=="reverse-inner":
        return [list(reversed(row)) for row in v]
    if axis=="transpose":
        return [list(row) for row in zip(*v)]
    if axis=="rot180":
        return [list(reversed(row)) for row in reversed(v)]
    return None


def _flip_program(axis):
    forms={
      "reverse-outer":"return x[::-1]",
      "reverse-inner":"return [row[::-1] for row in x]",
      "transpose":"return [list(row) for row in zip(*x)]",
      "rot180":"return [row[::-1] for row in x[::-1]]",
    }
    return validate_code("def transform(x):\n    "+forms[axis])


def _shift(v,dr,dc,bg):
    h=len(v); w=len(v[0])
    return [
        [v[r-dr][c-dc] if
          0<=r-dr<h and 0<=c-dc<w else bg
         for c in range(w)]
        for r in range(h)]


def _shift_program(dr,dc,bg):
    return validate_code(
        "def transform(x):\n"
        f"    dr={dr}\n    dc={dc}\n    bg={repr(bg)}\n"
        "    h=len(x)\n    w=len(x[0])\n"
        "    return [[x[r-dr][c-dc] if "
        "0<=r-dr<h and 0<=c-dc<w else bg "
        "for c in range(w)] for r in range(h)]")


def _move_label(v,label,dr,dc,bg):
    h=len(v);w=len(v[0])
    result=[list(row) for row in v]
    for r in range(h):
        for c in range(w):
            if type(v[r][c]) is type(label) and v[r][c]==label:
                result[r][c]=bg
    for r in range(h):
        for c in range(w):
            if type(v[r][c]) is type(label) and v[r][c]==label:
                nr,nc=r+dr,c+dc
                if 0<=nr<h and 0<=nc<w:
                    result[nr][nc]=label
    return result


def _move_label_program(label,dr,dc,bg):
    return validate_code(
        "def transform(x):\n"
        f"    color={repr(label)}\n"
        f"    dr={dr}\n    dc={dc}\n    bg={repr(bg)}\n"
        "    h=len(x)\n    w=len(x[0])\n"
        "    out=[row[:] for row in x]\n"
        "    for r in range(h):\n"
        "        for c in range(w):\n"
        "            if x[r][c]==color:\n"
        "                out[r][c]=bg\n"
        "    for r in range(h):\n"
        "        for c in range(w):\n"
        "            if x[r][c]==color:\n"
        "                nr=r+dr\n"
        "                nc=c+dc\n"
        "                if 0<=nr<h and 0<=nc<w:\n"
        "                    out[nr][nc]=color\n"
        "    return out")


def _propose_index_relationship(source_pairs,max_structural):
    if not _same_shape_sources(source_pairs,2):
        return []
    results=[]
    for axis in ("reverse-outer",):
        if all(source_same_value(_flip_transform(x,axis),y)
               for x,y in source_pairs):
            results.append(StructuralFactor(
                _flip_program(axis),"index-isomorphism/"+axis,
                6,len(source_pairs)))
    if not _same_shape_sources(source_pairs,3):
        return results
    for axis in ("reverse-inner","transpose","rot180"):
        if all(source_same_value(_flip_transform(x,axis),y)
               for x,y in source_pairs):
            results.append(StructuralFactor(
                _flip_program(axis),"index-isomorphism/"+axis,
                7,len(source_pairs)))
    # The relation is inferred from the SOURCE position changes rather than
    # a task label. Search a fixed generic bounded coordinate displacement.
    data=source_pairs
    labels=set()
    for x,y in data:
        labels.update(_flat(x))
    if len(labels)>20 or any(type(t) not in (int,str)
                             for t in labels):
        return results
    unique=sorted(labels,key=repr)
    modes=[_symbol_mode(x) for x,y in data]
    if any(mode is None for mode in modes):
        return results
    # A global displacement needs one common background value. The value
    # must be the modal SOURCE token in EACH independently authored example.
    if all(source_same_value(mode,modes[0]) for mode in modes):
        bg=modes[0]
        for dr in range(-4,5):
            for dc in range(-4,5):
                if dr==0 and dc==0:continue
                if all(source_same_value(
                    _shift(x,dr,dc,bg),y) for x,y in data):
                    results.append(StructuralFactor(
                        _shift_program(dr,dc,bg),
                        "index-translation",12,len(data)))
    if len(results)>=max_structural:
        return results[:max_structural]
    # Discover low description length *one token layer* motion. No color
    # or dimensionality is named by a benchmark, any rectangular sequence
    # of hashable typed values uses the identical source-only procedure.
    bg=modes[0]
    if not all(source_same_value(mode,bg) for mode in modes):
        return results
    for label in unique:
        if source_same_value(label,bg):continue
        for dr in range(-4,5):
            for dc in range(-4,5):
                if dr==0 and dc==0:continue
                if all(source_same_value(
                    _move_label(x,label,dr,dc,bg),y) for x,y in data):
                    results.append(StructuralFactor(
                        _move_label_program(label,dr,dc,bg),
                        "sparse-token-motion",15,len(data)))
                    if len(results)>=max_structural:
                        return results
    return results


def induce_structural_factors(source_pairs,*,max_candidates=12):
    """One generic representation-selection interface, only SOURCE pairs."""
    if not 2<=len(source_pairs)<=32 or not 1<=max_candidates<=64:
        raise ValueError("bounded, nonempty original SOURCE required")
    choices=_propose_leaf_relationship(source_pairs)
    choices.extend(_propose_index_relationship(
        source_pairs,max_structural=max_candidates))
    # Minimal description length controls overfit to a large categorical
    # table or a single hard-coded displacement. Same law on 1D and 2D.
    choices.sort(key=lambda item: (
        item.description_length,len(item.program),item.representation))
    result=[]
    hashes=set()
    for factor in choices:
        if factor.program in hashes:continue
        result.append(factor)
        hashes.add(factor.program)
        if len(result)>=max_candidates:break
    return tuple(result)
