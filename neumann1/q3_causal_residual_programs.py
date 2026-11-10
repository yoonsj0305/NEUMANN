"""Q3 source residual -> NEW executable multi-stage program synthesis.

The new hypothesis is generated from the REMAINING causal error of a
partially useful program, rather than selecting two independent programs
written from the original input/target pair. No benchmark dispatch,
target TEST gold, answer cache, or author ID conditions.

All executable SOURCE checks (including intermediates) use the existing
no-network IsolatedPython verifier. The returned program is *not* a
Q3 proof until independently SOURCE-certified outside this function and
then originally AUTHOR TEST scored after a SHA-frozen prediction.
"""
from __future__ import annotations

from hashlib import sha256

from .open_program_inventor import source_same_value
from .q3_source_residual_probes import induce_source_residual_probes
from .q3_structure_factorization import (
    StructuralFactor,induce_structural_factors)
from .q3_residual_composition import (
    induce_source_compositions,_sequential_code)
from .q3_object_graph_invention import induce_object_graph_factors


def _verified_output(runner,program,inputs):
    """Only no-network sandbox outputs count as executable evidence."""
    result=runner.evaluate(program,inputs)
    if result.status!="EXECUTED" or len(result.outputs)!=len(inputs):
        return None
    return tuple(result.outputs)


def induce_causal_residual_programs(
    source_pairs,runner,*,max_first=4,max_second=6,max_candidates=6
):
    """Induce stage2(Z)->Y *after* discovering stage1(X)->Z.

    Inputs are SOURCE training observations, never heldout SOURCE or TEST.
    The caller holds the independent SOURCE verifier's check examples.
    A full stage2 candidate is inferred from the ACTUAL stage1 outcomes,
    not guessed from original task targets in parallel.
    """
    if not (2<=len(source_pairs)<=32 and
            1<=max_first<=8 and 1<=max_second<=16 and
            1<=max_candidates<=16):
        raise ValueError("bounded original SOURCE grammar growth required")
    pairs=tuple((x,y) for x,y in source_pairs)
    inputs=[x for x,y in pairs]
    targets=[y for x,y in pairs]
    partials=induce_source_residual_probes(
        pairs,max_probes=max_first)
    out=[]
    distinct=set()
    for first in partials:
        intermediate=_verified_output(runner,first.program,inputs)
        if intermediate is None:
            continue
        # A complete first program is not a new causal-residual discovery.
        if all(source_same_value(a,b) for a,b in zip(intermediate,targets)):
            continue
        residual=tuple(zip(intermediate,targets))
        # Propose new operators FROM intermediate -> target.
        # The library is general and shared; the source-dependent
        # second operator is not a static replay of a known answer.
        proposals=(
            tuple(induce_source_residual_probes(
                residual,max_probes=max_second))
            +tuple(induce_source_compositions(
                residual,max_candidates=min(4,max_second)))
            +tuple(induce_structural_factors(
                residual,max_candidates=min(4,max_second)))
            +tuple(induce_object_graph_factors(
                residual,max_candidates=min(4,max_second)))
        )
        trials=0
        for second in proposals:
            if trials>=max_second:
                break
            trials+=1
            after=_verified_output(runner,second.program,intermediate)
            if after is None:
                continue
            if not all(source_same_value(a,b)
                       for a,b in zip(after,targets)):
                continue
            code=_sequential_code(first.program,second.program)
            digest=sha256(code.encode()).hexdigest()
            if digest in distinct:
                continue
            # The compiler is itself checked in Docker: nested lexical
            # scopes may not silently alter the composed program.
            combined=_verified_output(runner,code,inputs)
            if combined is None or not all(source_same_value(a,b)
                                          for a,b in zip(combined,targets)):
                continue
            distinct.add(digest)
            out.append(StructuralFactor(
                code,"source-induced-residual-causal-composition",
                first.description_length+second.description_length+1,
                len(pairs)))
            if len(out)>=max_candidates:
                return tuple(out)
    return tuple(out)
