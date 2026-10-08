"""Cheap public symbolic comparator with composed, checkable rewrite output.

It earns the same certificate rights as a future learned policy. It is a
deterministic baseline, not NEUMANN's learned structural intuition.
"""
from neumann1.representation_program import reachable_nodes, validate
from neumann1.representation_rewrite_certificate import rewrite_step


def propose(original, max_steps=32):
    validate(original)
    if type(max_steps) is not int or not 1 <= max_steps <= 32:
        raise ValueError("Bounded certificate search required")
    current = original
    steps = []
    for _ in range(max_steps):
        nodes = current["nodes"]
        selected = None
        for index in sorted(reachable_nodes(current), reverse=True):
            node = nodes[index]
            if node[0] not in {"add", "mul"}:
                continue
            left, right = nodes[node[1]], nodes[node[2]]
            if node[0] == "add":
                if left == ["const", 0] or right == ["const", 0]:
                    selected = ("ADD_ZERO", index)
                elif left[0] == right[0] == "mul" and set(left[1:]) & set(right[1:]):
                    selected = ("FACTOR_COMMON", index)
            elif left == ["const", 0] or right == ["const", 0]:
                selected = ("MUL_ZERO", index)
            elif left == ["const", 1] or right == ["const", 1]:
                selected = ("MUL_ONE", index)
            if selected:
                break
        if selected is None:
            break
        rule, target = selected
        current = rewrite_step(current, rule, target)
        steps.append({"rule": rule, "node": target})
    return {"candidate": current, "certificate": {"semantics": "exact_integer", "steps": steps},
            "learned": False, "oracle_used": False,
            "global_optimum_proven": False, "budget_exhausted": len(steps) == max_steps}
