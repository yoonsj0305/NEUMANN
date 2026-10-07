"""Public tensor-index state and checkable contraction programs.

Certifies index conservation for mathematical sum-product tensors. It does NOT
certify bit-identical IEEE results, actual dataset answers or measured speed.
Dense arithmetic counts and intermediate sizes are a planning model only.
"""
from collections import Counter
from math import prod


def validate_public(public):
    if not isinstance(public, dict) or set(public) != {"equation", "shapes"}:
        raise ValueError("Public equation/shapes only; no supplied path or answer")
    equation, shapes = public["equation"], public["shapes"]
    if not isinstance(equation, str) or equation.count("->") != 1 or "..." in equation:
        raise ValueError("Explicit registered tensor-index language required")
    left, output = equation.split("->")
    inputs = left.split(",")
    if not isinstance(shapes, list) or len(inputs) != len(shapes) or not 1 <= len(inputs) <= 1024:
        raise ValueError("Tensor/shape arity mismatch")
    sizes = {}
    for labels, shape in zip(inputs, shapes):
        if not isinstance(shape, list) or len(labels) != len(shape):
            raise ValueError("Index/shape arity mismatch")
        for label, size in zip(labels, shape):
            if label in {",", "-", ">"} or label.isspace() or type(size) is not int or not 1 <= size <= 1_000_000:
                raise ValueError("Invalid tensor dimension")
            if label in sizes and sizes[label] != size:
                raise ValueError("Inconsistent repeated-index dimension")
            sizes[label] = size
    if len(set(output)) != len(output) or not set(output) <= set(sizes):
        raise ValueError("Original output indices required")
    return inputs, output, sizes


def certify_path(public, path):
    inputs, output, sizes = validate_public(public)
    if not isinstance(path, (list, tuple)) or not 1 <= len(path) <= 2 * len(inputs):
        raise ValueError("Bounded nonempty contraction path required")
    active = [set(labels) for labels in inputs]
    counts = Counter(label for term in active for label in term)
    goal = set(output)
    work = 0
    largest = 0
    witness = []
    for step in path:
        if not isinstance(step, (list, tuple)) or not 1 <= len(step) <= len(active) or any(type(i) is not int or not 0 <= i < len(active) for i in step) or len(set(step)) != len(step):
            raise ValueError("Existing distinct tensor references required")
        union = set().union(*(active[i] for i in step))
        remaining_counts = counts.copy()
        for i in step:
            remaining_counts.subtract(active[i])
        kept = {label for label in union if label in goal or remaining_counts[label] > 0}
        removed = union - kept
        volume = prod(sizes[label] for label in union)
        # Same conventional dense arithmetic model as opt_einsum.helpers.flop_count.
        operations = volume * (max(1, len(step) - 1) + bool(removed))
        intermediate = prod(sizes[label] for label in kept)
        work += operations
        largest = max(largest, intermediate)
        witness.append({"consumed": list(step), "kept": sorted(kept), "summed": sorted(removed),
                        "dense_work": operations, "intermediate_elements": intermediate})
        for i in sorted(step, reverse=True):
            del active[i]
        active.append(kept)
        counts = remaining_counts
        counts.update(kept)
    if len(active) != 1 or active[0] != goal:
        raise ValueError("Path does not terminate at the original tensor goal")
    return {"accepted": True, "authority": "INDEX_CONSERVATION_SUM_PRODUCT_PATH",
            "dense_arithmetic_work_model": work, "largest_intermediate_elements": largest,
            "ordered_output": output, "witness": witness,
            "numerical_dataset_answer_verified": False, "IEEE_bit_identity_claimed": False}


def is_matrix_chain(public):
    inputs, output, _ = validate_public(public)
    if len(inputs) < 2 or any(len(term) != 2 or term[0] == term[1] for term in inputs):
        return False
    counts = Counter(label for term in inputs for label in term)
    if len(counts) != len(inputs) + 1 or any(c not in (1, 2) for c in counts.values()) or set(output) != {x for x, c in counts.items() if c == 1} or len(output) != 2:
        return False
    adjacency = {x: set() for x in counts}
    for a, b in inputs:
        adjacency[a].add(b); adjacency[b].add(a)
    seen, pending = set(), [next(iter(counts))]
    while pending:
        node = pending.pop()
        if node not in seen:
            seen.add(node); pending.extend(adjacency[node] - seen)
    return len(seen) == len(counts)


def public_plan(public, strategy):
    import opt_einsum as oe
    if oe.__version__ != "3.4.0" or strategy not in {"greedy", "auto", "auto-hq", "random-greedy-128", "dynamic-programming"}:
        raise ValueError("Pinned mature planner and declared strategy required")
    validate_public(public)
    if strategy == "dynamic-programming" and len(public["shapes"]) > 16 and not is_matrix_chain(public):
        raise ValueError("DP exceeds predeclared public topology/operand budget")
    path, info = oe.contract_path(public["equation"], *[tuple(s) for s in public["shapes"]],
                                  shapes=True, optimize=strategy)
    result = certify_path(public, path)
    if result["dense_arithmetic_work_model"] != int(info.opt_cost):
        raise ValueError("Independent arithmetic model disagrees with reused planner")
    return {"path": [list(step) for step in path], "certificate": result,
            "oracle_used": False, "learned": False}
