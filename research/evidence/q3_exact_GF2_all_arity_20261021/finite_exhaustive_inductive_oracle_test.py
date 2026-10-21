"""Independent finite-state exhaustive oracle for the Q3 affine CEGIS fixed point.

For 3 Boolean state bits, enumerate EVERY affine subset of 8 concrete states
and select the smallest that contains ALL actual Pre states and is closed under
ALL actual edges. Unlike the production solver, this oracle never uses SMT
reasoning about reachability or algebraic nullspace construction.
"""
import itertools
import random
import z3

from research.evidence.q3_exact_GF2_all_arity_20261021.dragon2_exact_affine_inductive_fixpoint import converge


def affine_subset(values):
    if not values:
        return False
    origin = min(values)
    offsets = {v ^ origin for v in values}
    return all(a ^ b in offsets for a in offsets for b in offsets)


def all_affine_subsets(n):
    universe = tuple(range(1 << n))
    return [
        frozenset(x for x in universe if (bitset >> x) & 1)
        for bitset in range(1, 1 << (1 << n))
        if affine_subset({x for x in universe if (bitset >> x) & 1})
    ]


def smt_cube(xs, value):
    return z3.And(*[xs[i] if (value >> i) & 1 else z3.Not(xs[i])
                    for i in range(len(xs))])


def concrete_from_kernel(gf2_basis, n):
    mask = (1 << n) - 1
    return frozenset(
        x for x in range(1 << n)
        if all(((v & mask) & x).bit_count() % 2 == ((v >> n) & 1)
               for v in gf2_basis)
    )


def reference(pre, edges, affine_sets):
    admissible = [s for s in affine_sets
                  if pre.issubset(s) and
                  all(b in s for a, b in edges if a in s)]
    if not admissible:
        raise RuntimeError("REFERENCE_WITHOUT_UNIVERSAL_AFFINE_SPACE")
    least = set.intersection(*map(set, admissible))
    if not affine_subset(least):
        raise RuntimeError("REFERENCE_INTERSECTION_NOT_AFFINE")
    return frozenset(least)


def check_case(case_id, pre, edges, spaces):
    n = 3
    a = z3.Bools("a0 a1 a2")
    b = z3.Bools("b0 b1 b2")
    raw_pre = z3.Or(*[smt_cube(a, p) for p in sorted(pre)])
    raw_trans = z3.Or(*[
        z3.And(smt_cube(a, u), smt_cube(b, v))
        for u, v in sorted(edges)
    ])
    actual = converge(raw_pre, raw_trans, a, b, list(range(n)), 20000)
    if actual["status"] != "Z3_EXACT_LEAST_AFFINE_FIXEDPOINT_OBTAINED":
        raise RuntimeError(f"CONTROL_CASE_{case_id}_ABSTAIN_{actual['status']}")
    found = concrete_from_kernel(actual["complete_affine_GF2_kernel_vectors"], n)
    expected = reference(pre, edges, spaces)
    if found != expected:
        raise AssertionError(f"CASE_{case_id}_INCORRECT expected={sorted(expected)} got={sorted(found)}")
    return actual["GF2_complete_inductive_affine_kernel_nullity"]


def main():
    spaces = all_affine_subsets(3)
    if len(spaces) != 51:
        raise RuntimeError("INDEPENDENT_AFFINE_ORACLE_SPACE_COUNT_NOT_51")
    rng = random.Random(20261021)
    cases = [
        ({0}, set()),
        (set(range(8)), set()),
        ({0}, {(u, v) for u in range(8) for v in range(8)}),
        ({0}, {(u, v) for u in range(8) for v in range(8)
               if u.bit_count() % 2 == v.bit_count() % 2}),
    ]
    for _ in range(16):
        pre = set(rng.sample(range(8), rng.randint(1, 4)))
        edges = {(u, v) for u in range(8) for v in range(8)
                 if rng.randrange(4) == 0}
        cases.append((pre, edges))
    actual_dims = [
        check_case(i, pre, edges, spaces)
        for i, (pre, edges) in enumerate(cases)
    ]
    assert len(actual_dims) == 20
    print("INDEPENDENT_EXHAUSTIVE_AFFINE_3BIT_REFERENCE",
          "PASS", len(actual_dims), "/20")
    print("AFFINE_REFERENCE_SPACES", len(spaces))
    print("CHECKED_KERNEL_NULLITIES", actual_dims)


if __name__ == "__main__":
    main()
