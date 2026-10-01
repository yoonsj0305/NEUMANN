"""v0.0.95 semantic-authority boundary for the v0.0.94 compact graph route.

The point selector chooses exactly 2m columns.  The compact graph receives only
those columns and returns a 2m shortlist, so the downstream restricted LP has
the same variable support as point-only, up to a permutation.  This module
makes that boundary explicit without running a model, solver, or timer.
"""


def canonical_support(indices):
    values = tuple(indices)
    if any(type(i) is not int or i < 0 for i in values):
        raise ValueError("invalid support index")
    if len(values) != len(set(values)):
        raise ValueError("duplicate support index")
    return tuple(sorted(values))


def permutation_from(reference, reordered):
    """Return positions that reorder reference into reordered.

    Raises when the two lists do not contain exactly the same unique indices.
    """
    ref = tuple(reference)
    other = tuple(reordered)
    if canonical_support(ref) != canonical_support(other) or len(ref) != len(other):
        raise ValueError("supports differ")
    pos = {value: i for i, value in enumerate(ref)}
    return tuple(pos[value] for value in other)


def authority_boundary(point_proposal, compact_proposal):
    """Classify the semantic delta between point-only and compact-graph routes."""
    point_support = canonical_support(point_proposal["shortlist"])
    compact_support = canonical_support(compact_proposal["shortlist"])
    support_equivalent = point_support == compact_support
    point_basis = canonical_support(point_proposal["basis"])
    compact_basis = canonical_support(compact_proposal["basis"])
    basis_equivalent = point_basis == compact_basis
    if not support_equivalent:
        delta = "SUPPORT_CHANGED"
    elif basis_equivalent:
        delta = "ORDER_ONLY"
    else:
        delta = "EXACT_M_BASIS_OR_ORDER_ONLY"
    return {
        "restricted_support_equivalent": support_equivalent,
        "basis_equivalent": basis_equivalent,
        "semantic_delta": delta,
    }


DECISION = "STOP_SAME_SUPPORT_GRAPH_REFINEMENT_NO_NEW_FIT"
GLOBAL_Q3 = "OPEN"
GLOBAL_Q4 = "OPEN"
