"""Construct a reusable Boolean METHOD from tiny solved source functions.

Only NAND is built into the circuit DSL. From complete arity-2 and arity-3
ground truth, induce base B and the previously unspecified transition H;
verify the derived constructor on arity-4 SOURCE, then extrapolate.

All extrapolation is CONDITIONAL on a one-bit fold recurrence. Neither source
fit nor the arity-4 check proves that arbitrary black-box programs recur.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product


class InsufficientEvidence(ValueError):
    pass


def _truth_table(bits, arity):
    if len(bits) != 1 << arity:
        raise ValueError("complete source truth table required")
    return sum(value << i for i, value in enumerate(bits))


def _compile_nand(mask):
    width = 4
    allones = (1 << width) - 1
    # Source bit order is (0,0), (0,1), (1,0), (1,1).
    # Compact semantic enumeration searches ALL sixteen binary Boolean maps,
    # synthesizing every circuit using only NAND and input variables.
    best = {0b1100: (1, ("arg", 0)),
            0b1010: (1, ("arg", 1))}
    while True:
        changed = False
        for ma, (ca, ea) in tuple(best.items()):
            for mb, (cb, eb) in tuple(best.items()):
                m = ~(ma & mb) & allones
                size = ca + cb + 1
                if m not in best or size < best[m][0]:
                    best[m] = (size, ("nand", ea, eb))
                    changed = True
        if not changed:
            break
    if len(best) != 16:
        raise AssertionError("universal NAND basis was not generated")
    return best[mask][1], best[mask][0] - 1


def _run(circuit, args):
    if circuit[0] == "arg":
        return args[circuit[1]]
    return 1 - (_run(circuit[1], args) & _run(circuit[2], args))


@dataclass(frozen=True)
class InventedFoldMethod:
    base_circuit: tuple
    extension_circuit: tuple
    base_table: tuple[int, ...]
    extension_table: tuple[int, ...]
    base_gate_count: int
    extension_gate_count: int
    source_observations: int
    source_lengths: tuple[int, ...]
    recurrence_hypothesis: str = "f(n+1)=H(f(n),new_input)"
    validation_exact: bool = True
    unconditional_for_arbitrary_functions: bool = False

    def apply(self, values):
        bits = tuple(values)
        if len(bits) < 2 or any(type(b) is not int or b not in (0, 1)
                                for b in bits):
            raise InsufficientEvidence("Boolean sequence of arity >= 2 required")
        state = _run(self.base_circuit, bits[:2])
        for bit in bits[2:]:
            state = _run(self.extension_circuit, (state, bit))
        return state

    def fingerprint(self):
        return (self.base_table, self.extension_table)


def invent_boolean_fold(source_oracle, *, source_lengths=(2, 3, 4),
                        max_source_queries=28):
    """Invent a constructor from source programs, never target outputs.

    28 exact source calls: 4 + 8 + 16. B must be surjective so the
    four entries of H are determined by arity-3, not guessed or hardcoded.
    """
    if tuple(source_lengths) != (2, 3, 4):
        raise InsufficientEvidence("source contract requires arities 2,3,4")
    if max_source_queries < 0:
        raise ValueError("negative budget")
    facts = {}
    for arity in source_lengths:
        truth = {}
        for bits in product((0, 1), repeat=arity):
            if len(facts) >= max_source_queries:
                raise InsufficientEvidence("source oracle budget exhausted")
            value = source_oracle(bits)
            if type(value) is not int or value not in (0, 1):
                raise InsufficientEvidence("exact Boolean source oracle required")
            facts[bits] = value
            truth[bits] = value
        if arity == 2:
            base = truth
        elif arity == 3:
            triple = truth
    base_table = tuple(base[bits] for bits in product((0, 1), repeat=2))
    if len(set(base_table)) != 2:
        raise InsufficientEvidence("base does not expose both fold states")
    transition = {}
    for (x, y, z), output in triple.items():
        key = (base[x, y], z)
        if key in transition and transition[key] != output:
            raise InsufficientEvidence("one-bit extension law contradicted")
        transition[key] = output
    if len(transition) != 4:
        raise InsufficientEvidence("extension underidentified")
    transition_table = tuple(
        transition[bits] for bits in product((0, 1), repeat=2))
    base_circuit, base_gates = _compile_nand(_truth_table(base_table, 2))
    extension_circuit, extension_gates = _compile_nand(
        _truth_table(transition_table, 2))
    method = InventedFoldMethod(
        base_circuit, extension_circuit, base_table, transition_table,
        base_gates, extension_gates, len(facts), tuple(source_lengths))
    for bits, output in facts.items():
        if method.apply(bits) != output:
            raise InsufficientEvidence(
                "new program constructor falsified on source examples")
    return method
