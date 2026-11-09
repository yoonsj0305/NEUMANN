"""Q3: SOURCE-only discovery of hidden-state operators (a minimal DFA).

Learns an executable *new state space and transitions* from membership I/O.
Neither hidden states, transitions, example solution programs, nor target labels
are provided to the learner.  The alphabet and an upper bound N on the true
number of deterministic states are externally supplied structural assumptions.

Theorem (conditional): If the unknown function is recognized by a complete
DFA with <=N states, signatures of all reachable prefixes of length <N
against all suffixes of length <N identify the minimal machine.  Probing one
more input symbol constructs all transitions.  All future input lengths then
follow by induction. This is a classical Myhill--Nerode construction, not a
claim of a newly discovered mathematical theorem or unrestricted AGI.

Finite membership observations can never prove the unknown function belongs
to the assumed DFA class; e.g. a delayed exceptional word can fool a bounded
experiment. The conditional nature is an explicit part of the output.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from time import perf_counter_ns
from typing import Callable


class MissingStateEvidence(ValueError):
    """Abstain when source assumptions or finite budgets cannot be certified."""


def _words(alphabet: tuple[str, ...], max_length: int):
    yield ""
    for length in range(1, max_length + 1):
        for symbols in product(alphabet, repeat=length):
            yield "".join(symbols)


@dataclass(frozen=True)
class InventedStateOperator:
    alphabet: tuple[str, ...]
    state_signatures: tuple[tuple[int, ...], ...]
    representatives: tuple[str, ...]
    transitions: tuple[tuple[int, ...], ...]
    accepting_states: frozenset[int]
    state_bound: int
    source_queries: int
    independent_source_checks: int
    elapsed_ms: float

    @property
    def state_count(self) -> int:
        return len(self.state_signatures)

    @property
    def ast(self):
        return (
            "source_invented_latent_finite_state_operator",
            ("discovered_minimal_states", self.state_count),
            ("discovered_transition_table", self.transitions),
            ("discovered_acceptance", tuple(sorted(self.accepting_states))),
        )

    @property
    def conditional_proof(self) -> str:
        return (
            "If the source behavior is a complete deterministic finite-state "
            f"language with at most {self.state_bound} states, every state is "
            "reachable by a word shorter than that bound and every pair of "
            "different states is distinguished by a suffix shorter than the "
            "bound. The measured residual signatures therefore identify the "
            "minimal states and each transition; induction proves all lengths. "
            "The state-bound/class assumption is not identified from finite I/O."
        )

    def state_trace(self, word: str) -> tuple[int, ...]:
        if type(word) is not str:
            raise TypeError("a symbolic word is required")
        lookup = {character: i for i, character in enumerate(self.alphabet)}
        state = 0
        history = [state]
        for character in word:
            if character not in lookup:
                raise MissingStateEvidence("input outside frozen alphabet")
            state = self.transitions[state][lookup[character]]
            history.append(state)
        return tuple(history)

    def apply(self, word: str) -> int:
        return int(self.state_trace(word)[-1] in self.accepting_states)


@dataclass(frozen=True)
class StateDiscovery:
    status: str
    program: InventedStateOperator | None
    queried_source_words: int
    inferred_states: int
    elapsed_ms: float
    note: str

    def apply(self, word: str) -> int:
        if self.program is None:
            raise MissingStateEvidence("not source certified: "+self.status)
        return self.program.apply(word)


class UnknownStateOperatorInventor:
    def __init__(self, *, max_states=4, max_queries=10000,
                 max_source_ms=15000):
        if (type(max_states) is not int or not 1 <= max_states <= 7
                or type(max_queries) is not int or not 1 <= max_queries <= 100000
                or type(max_source_ms) not in (int, float)
                or not 1 <= max_source_ms <= 120000):
            raise ValueError("finite symbolic state-discovery budgets required")
        self.max_states = max_states
        self.max_queries = max_queries
        self.max_source_ms = max_source_ms

    def invent(
            self, source_membership: Callable[[str], int], *,
            alphabet=("0", "1"), independent_source_checks=(),
            known_classical=None, forbidden_target_words=()):
        start = perf_counter_ns()
        if (not callable(source_membership)
                or type(alphabet) not in (tuple, list)
                or not 1 <= len(alphabet) <= 4
                or any(type(a) is not str or len(a) != 1 for a in alphabet)
                or len(set(alphabet)) != len(alphabet)):
            raise ValueError("explicit, distinct, one-character SOURCE alphabet")
        alphabet = tuple(alphabet)
        checks = tuple(independent_source_checks)
        forbidden = frozenset(forbidden_target_words)
        if any(type(w) is not str or
               any(letter not in alphabet for letter in w) or
               type(y) is not int or y not in (0, 1)
               for w, y in checks):
            raise ValueError("well-typed binary independent SOURCE checks required")
        if len({w for w, _ in checks}) != len(checks):
            raise ValueError("source verifier inputs must be distinct")

        def result(status, program, queries, note):
            return StateDiscovery(
                status, program, queries,
                0 if program is None else program.state_count,
                (perf_counter_ns() - start) / 1e6, note)

        # Classical-first on a separately source-certified contract.
        if (known_classical is not None and len(checks) >= 3
                and all(known_classical(w) == y for w, y in checks)):
            return result("CLASSICAL_FIRST", None, 0,
                          "trusted classical candidate passed source checks")

        n = self.max_states
        # Every query is an input of length <=2N-1. SOURCE vs target separation:
        # a target input cannot be silently used for source experiment queries.
        prefixes = tuple(_words(alphabet, n - 1))
        edges = tuple(_words(alphabet, n))
        suffixes = tuple(_words(alphabet, n - 1))
        all_needed = frozenset(p+s for p in edges for s in suffixes)
        if forbidden.intersection(all_needed):
            return result("ABSTAIN_TARGET_OVERLAP", None, 0,
                          "a requested SOURCE probe is a forbidden target")
        if len(all_needed) > self.max_queries:
            return result("ABSTAIN_QUERY_BUDGET", None, 0,
                          "full finite source-identification basis exceeds budget")

        cache: dict[str, int] = {}
        deadline = start + int(self.max_source_ms * 1_000_000)

        def ask(word):
            if word in cache:
                return cache[word]
            if perf_counter_ns() > deadline:
                raise MissingStateEvidence("ABSTAIN_TIME_BUDGET")
            try:
                ans = source_membership(word)
            except (ValueError, TypeError, KeyError, OverflowError) as exc:
                raise MissingStateEvidence("ABSTAIN_SOURCE_ORACLE_ERROR") from exc
            if type(ans) is not int or ans not in (0, 1):
                raise MissingStateEvidence("ABSTAIN_NONBINARY_SOURCE")
            cache[word] = ans
            return ans

        try:
            # Lexicographic canonical residual signatures. No state labels
            # or state number are supplied by the unknown oracle.
            def signature(prefix):
                return tuple(ask(prefix+s) for s in suffixes)

            state_signatures = []
            representatives = []
            state_ids = {}
            for p in prefixes:
                sig = signature(p)
                if sig not in state_ids:
                    state_ids[sig] = len(state_signatures)
                    state_signatures.append(sig)
                    representatives.append(p)
            if len(state_signatures) > n:
                return result("ABSTAIN_STATE_BOUND_FALSIFIED", None,
                              len(cache), "more distinct residuals than N")

            rows = []
            for p in representatives:
                row = []
                for a in alphabet:
                    sig = signature(p+a)
                    if sig not in state_ids:
                        return result("ABSTAIN_STATE_BOUND_FALSIFIED", None,
                                      len(cache),
                                      "unrepresented transition residual")
                    row.append(state_ids[sig])
                rows.append(tuple(row))

            # Every representative and other source prefix of same residual
            # must lead to the SAME next-state signature on each symbol.
            for p in prefixes:
                src = state_ids[signature(p)]
                for k, a in enumerate(alphabet):
                    if state_ids.get(signature(p+a)) != rows[src][k]:
                        return result("ABSTAIN_NONCONGRUENT_SOURCE", None,
                                      len(cache),
                                      "hypothesized state equivalence fails")
            acceptance = frozenset(
                i for i, sig in enumerate(state_signatures) if sig[0] == 1)
            invented = InventedStateOperator(
                alphabet, tuple(state_signatures), tuple(representatives),
                tuple(rows), acceptance, n, len(cache), len(checks),
                (perf_counter_ns() - start)/1e6)
            # Checks never enter the candidate's state inference. They are
            # external independent SOURCE tests, not heldout TARGET gold.
            if any(invented.apply(w) != y for w, y in checks):
                return result("ABSTAIN_SOURCE_COUNTEREXAMPLE", None,
                              len(cache), "source falsifies bounded DFA prior")
            return result("SOURCE_CERTIFIED_CONDITIONAL_DFA", invented,
                          len(cache),
                          "exact all-length transfer CONDITIONAL on <=N DFA")
        except MissingStateEvidence as exc:
            return result(str(exc), None, len(cache),
                          "source experiment could not be completed")
