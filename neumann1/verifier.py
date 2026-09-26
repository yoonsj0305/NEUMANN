from __future__ import annotations
from typing import Any
from .types import Problem, Representation, IRKind, VerificationResult, CostLedger


class DeterministicVerifier:
    def verify(self, problem: Problem, representation: Representation, answer: Any, ledger: CostLedger) -> VerificationResult:
        ledger.verification_steps += 1

        if representation.kind == IRKind.UNKNOWN:
            return VerificationResult(False, "UNKNOWN representation cannot be verified")

        if representation.kind == IRKind.BIPARTITE_MATCHING:
            left = set(representation.payload["left"])
            edges = representation.payload["edges"]
            assignment = answer.get("assignment", {})
            if set(assignment) - left:
                return VerificationResult(False, "assignment contains unknown left node")
            used = set()
            for u, v in assignment.items():
                ledger.verification_steps += 1
                if v not in edges.get(u, []):
                    return VerificationResult(False, f"invalid edge {u}->{v}")
                if v in used:
                    return VerificationResult(False, f"right node reused: {v}")
                used.add(v)
            if answer.get("perfect") and len(assignment) != len(left):
                return VerificationResult(False, "perfect flag inconsistent with assignment")
            return VerificationResult(True, "matching constraints verified")

        if representation.kind == IRKind.SHORTEST_PATH:
            path = answer.get("path")
            if path is None:
                return VerificationResult(True, "no path result accepted in scaffold")
            graph = representation.payload["graph"]
            total = 0.0
            for a, b in zip(path, path[1:]):
                ledger.verification_steps += 1
                candidates = [w for v, w in graph[a] if v == b]
                if not candidates:
                    return VerificationResult(False, f"path edge missing: {a}->{b}")
                total += min(candidates)
            if abs(total - float(answer["distance"])) > 1e-9:
                return VerificationResult(False, "reported distance does not match path")
            return VerificationResult(True, "path feasibility and cost verified")

        if representation.kind == IRKind.LINEAR_SYSTEM:
            A = representation.payload["A"]
            b = representation.payload["b"]
            names = representation.payload.get("variables") or [f"x{i}" for i in range(len(b))]
            for row, target in zip(A, b):
                ledger.verification_steps += len(row)
                lhs = sum(float(c) * float(answer[n]) for c, n in zip(row, names))
                if abs(lhs - float(target)) > 1e-7:
                    return VerificationResult(False, "solution violates linear equation")
            return VerificationResult(True, "linear equations verified")

        return VerificationResult(False, "No verifier for representation kind")
