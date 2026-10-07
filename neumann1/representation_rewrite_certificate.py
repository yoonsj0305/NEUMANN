"""Checkable composed rewrite interface for a future perspective policy.

Known integer-ring rules are reused infrastructure, not a learned mechanism or
new science. A certificate preserves the original ordered goal at every step.
No global polynomial expansion, Oracle, CAS confidence or sampled acceptance.
"""
from time import perf_counter

from neumann1.representation_program import Builder, ProgramError, validate

RULES = {"FACTOR_COMMON", "DISTRIBUTE_LEFT", "ADD_ZERO", "MUL_ONE", "MUL_ZERO",
         "SWAP_ADD", "SWAP_MUL", "ASSOC_ADD", "ASSOC_MUL"}


def rewrite_step(original, rule, target):
    validate(original)
    if rule not in RULES or type(target) is not int or not 0 <= target < len(original["nodes"]):
        raise ProgramError("Registered rule and current node required")
    nodes = original["nodes"]
    node = nodes[target]
    builder = Builder(original["inputs"])
    memo = {}

    def emit(index):
        if index in memo:
            return memo[index]
        current = nodes[index]
        if index == target:
            result = replacement()
        elif current[0] == "input":
            result = builder.input(current[1])
        elif current[0] == "const":
            result = builder.const(current[1])
        else:
            result = builder.node(current[0], emit(current[1]), emit(current[2]))
        memo[index] = result
        return result

    def replacement():
        kind = node[0]
        if kind not in {"add", "mul"}:
            raise ProgramError("Rule does not match an arithmetic node")
        left, right = node[1:]
        if rule in {"SWAP_ADD", "SWAP_MUL"} and kind == rule[5:].lower():
            return builder.node(kind, emit(right), emit(left))
        if rule in {"ASSOC_ADD", "ASSOC_MUL"} and kind == rule[6:].lower() and nodes[left][0] == kind:
            a, b = nodes[left][1:]
            return builder.node(kind, emit(a), builder.node(kind, emit(b), emit(right)))
        if rule == "FACTOR_COMMON" and kind == "add" and nodes[left][0] == nodes[right][0] == "mul":
            lhs, rhs = nodes[left][1:], nodes[right][1:]
            for li in (0, 1):
                for ri in (0, 1):
                    if lhs[li] == rhs[ri]:
                        return builder.mul(emit(lhs[li]), builder.add(emit(lhs[1 - li]), emit(rhs[1 - ri])))
        if rule == "DISTRIBUTE_LEFT" and kind == "mul" and nodes[right][0] == "add":
            a, b = nodes[right][1:]
            return builder.add(builder.mul(emit(left), emit(a)), builder.mul(emit(left), emit(b)))
        constant = lambda i, value: nodes[i] == ["const", value]
        if rule == "ADD_ZERO" and kind == "add":
            if constant(left, 0):
                return emit(right)
            if constant(right, 0):
                return emit(left)
        if rule == "MUL_ONE" and kind == "mul":
            if constant(left, 1):
                return emit(right)
            if constant(right, 1):
                return emit(left)
        if rule == "MUL_ZERO" and kind == "mul" and (constant(left, 0) or constant(right, 0)):
            return builder.const(0)
        raise ProgramError("Rule premise is false; certificate rejected")

    result = builder.finish([emit(output) for output in original["outputs"]])
    if target not in memo:
        raise ProgramError("Rewrite target is not reachable from the original goal")
    return result


def check_certificate(original, candidate, certificate):
    start = perf_counter()
    try:
        validate(original); validate(candidate)
        if not isinstance(certificate, dict) or set(certificate) != {"semantics", "steps"} or certificate["semantics"] != "exact_integer":
            raise ProgramError("Exact certificate schema required")
        steps = certificate["steps"]
        if not isinstance(steps, list) or not 1 <= len(steps) <= 32:
            raise ProgramError("Certificate step budget required")
        current = original
        for step in steps:
            if not isinstance(step, dict) or set(step) != {"rule", "node"}:
                raise ProgramError("Rule/node only; no executable or Oracle payload")
            current = rewrite_step(current, step["rule"], step["node"])
        if candidate != current:
            raise ProgramError("Candidate does not match the verified final representation")
        return {"accepted": True, "authority": "COMPOSED_EXACT_INTEGER_RING_REWRITE_CERTIFICATE",
                "steps_checked": len(steps), "verification_seconds": perf_counter() - start,
                "learned": False, "oracle_used": False}
    except (ProgramError, RecursionError, TypeError) as exc:
        return {"accepted": False, "authority": "NOT_VERIFIED", "error": str(exc),
                "verification_seconds": perf_counter() - start}
