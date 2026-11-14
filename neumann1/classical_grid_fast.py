"""Output-identical elimination of redundant work in the 626-program grammar.

`arc2_meta_grid_reasoner.fit_task(demo, range(626), 626, max_hits=626)`
(the call the hybrid and the routers make) recomputes every program on every
demonstration from scratch, then compares.  Three pieces of that work are
provably unnecessary because every operator is a pure function of its grid:

1. Shared prefixes. 600 of the 626 programs are pairs (x, y).  The first
   stage `apply(input, x)` depends only on (input, x), so it is computed once
   per demonstration instead of up to 24 times.
2. Duplicate intermediates.  Different operators often produce the SAME grid
   (on a 1 x N row: identity == flip_ud, transpose == rotate90 ...).
   `apply(grid, y)` is memoized on the grid VALUE.
3. Early rejection.  A program fits iff every demonstration matches exactly
   or through ONE consistent colour map.  A shape mismatch or colour-map
   conflict on any demonstration rejects it, so later demonstrations are not
   executed.  (The original code executes all demonstrations first.)

`fit_all(demo)` returns exactly the same `(winners, checks)` as the original
full scan: same program indices, same order, same adapter kind and the same
colour mapping.  This is checked against the original on every task by the
evaluation harness and by tests; it is an exactness claim, not an estimate.
"""
from __future__ import annotations
from . import arc2_meta_grid_reasoner as old

N_PROGRAMS = len(old.PROGRAMS)


def _same_shape(a, b):
    return len(a) == len(b) and len(a[0]) == len(b[0])


def fit_all(demo):
    """Equivalent of old.fit_task(demo, range(626), 626, max_hits=626)."""
    memo = {}

    def run(grid, op):
        key = (grid, op)
        if key in memo:
            return memo[key]
        out = old.apply(grid, op)
        memo[key] = out
        return out

    inputs = [x for x, _ in demo]
    targets = [y for _, y in demo]
    winners = []
    for idx, program in enumerate(old.PROGRAMS):
        exact = True
        mapping = {}
        ok = True
        for grid, target in zip(inputs, targets):
            out = grid
            for op in program:
                out = run(out, op)
                if out is None:
                    break
            if out is None or not _same_shape(out, target):
                ok = False
                break
            if exact and out != target:
                exact = False
            # Same insertion order as old.fit_color_map over all demos.
            for orow, trow in zip(out, target):
                for a, b in zip(orow, trow):
                    prev = mapping.get(a)
                    if prev is None:
                        mapping[a] = b
                    elif prev != b:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if not ok:
            continue
        if exact:
            winners.append((idx, {"kind": "exact", "mapping": {}}))
        else:
            winners.append((idx, {"kind": "recolor", "mapping": mapping}))
    return winners, N_PROGRAMS


def classical_candidates(demo, inputs, limit=2):
    """Same candidates as source_learned_grid_router._classical, faster."""
    from .hybrid_arc_grid_inventor import GridCandidate
    matches, checks = fit_all(demo)
    ordered = sorted(matches, key=lambda item: (
        item[1]["kind"] != "exact", len(old.PROGRAMS[item[0]]), item[0]))
    proposed, seen = [], set()
    for i, adapter in ordered:
        outputs = []
        for inp in inputs:
            out = old.predict(inp, old.PROGRAMS[i])
            if out is not None and adapter["kind"] == "recolor":
                out = old.recolor(out, adapter["mapping"])
            outputs.append(out)
        key = tuple(outputs)
        if key in seen:
            continue
        seen.add(key)
        proposed.append(GridCandidate(
            origin="source_classical_grid_grammar", program_id=int(i),
            outputs=key, expression=None))
        if len(proposed) == limit:
            break
    return tuple(proposed), checks, bool(matches)
