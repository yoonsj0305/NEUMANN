"""Indexed canonical De Bruijn cyclic-subword membership, exact drop-in replacement.

A length-W De Bruijn word contains every k-ary W-tuple exactly once around its
cycle. For fragment length >= W there is at most ONE possible starting phase:
look it up in O(1), then verify the remaining elements. Prior implementation
scans all n=k**W phases and replays whole fragment for each.
No model class, solver parameters or prediction rules are changed.
"""
import functools
import debruijn_structural_model as original
FROZEN_ORIGINAL_FN=original.occurs_on_cycle

@functools.lru_cache(maxsize=32)
def index(cycle):
    n=len(cycle)
    k=max(cycle)+1
    assert k>=2
    order=0;power=1
    while power<n:
        power*=k
        order+=1
    assert power==n and order>=1
    starts={}
    for phase in range(n):
        fragment=tuple(cycle[(phase+j)%n] for j in range(order))
        if fragment in starts:
            # No uniqueness: we must NOT use the index as an authority.
            return (order,None)
        starts[fragment]=phase
    assert len(starts)==n
    return (order,starts)

def indexed_occurs_on_cycle(fragment,cycle):
    n=len(cycle)
    W,starts=index(cycle)
    if len(fragment)<W or starts is None:
        return FROZEN_ORIGINAL_FN(fragment,cycle)
    phase=starts.get(tuple(fragment[:W]))
    if phase is None:return False
    return all(v==cycle[(phase+j)%n] for j,v in enumerate(fragment))

def infer_indexed(task):
    old=original.occurs_on_cycle
    original.occurs_on_cycle=indexed_occurs_on_cycle
    try:
        return original.infer(task)
    finally:
        original.occurs_on_cycle=old

def equivalence_theorem_exhaustive():
    # Exhaustive k-ary sequences of length <=W+2 for small k/W against original.
    import itertools
    counts=0
    for k,W in ((2,3),(2,5),(3,3)):
        cyc=original.debruijn(k,W)
        for L in range(W+3):
            for seq in itertools.product(range(k),repeat=L):
                a=FROZEN_ORIGINAL_FN(seq,cyc)
                b=indexed_occurs_on_cycle(seq,cyc)
                assert a==b,(k,W,seq,a,b)
                counts+=1
    return counts
