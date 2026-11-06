"""Classical, bounded-state W-method for RC39 membership-only Mealy conformance.

The accepted test language is (P union P·Sigma) Sigma^[0..N-m] W.
P covers every candidate state; W distinguishes every pair of candidate states;
m is the candidate's reachable, distinguishable state count; N is a trusted
upper bound on UNKNOWN reference states. Every reference access is charged.
If the contract is absent, the result is UNKNOWN, never all-length PASS.

This is a known classical W-method, not autonomous architecture invention.
"""
from collections import deque
from dataclasses import dataclass
from itertools import product

from research.q3.rc39.active_mealy import UnknownStateStructure


class WMethodUnknown(UnknownStateStructure):
    pass


def state_cover(machine):
    seen = {machine.initial: ""}
    queue = deque([machine.initial])
    while queue:
        q = queue.popleft()
        for index, symbol in enumerate(machine.alphabet):
            nxt = machine.transitions[q][index]
            if nxt not in seen:
                seen[nxt] = seen[q] + symbol
                queue.append(nxt)
    if len(seen) != len(machine.transitions):
        raise WMethodUnknown("UNREACHABLE_HYPOTHESIS_STATE")
    return tuple(seen.values())


def separating_word(machine, left, right):
    queue = deque([(left, right, "")])
    visited = {(left, right)}
    while queue:
        s, t, prefix = queue.popleft()
        for i, a in enumerate(machine.alphabet):
            w = prefix + a
            if machine.emissions[s][i] != machine.emissions[t][i]:
                return w
            pair = (machine.transitions[s][i], machine.transitions[t][i])
            if pair not in visited:
                visited.add(pair)
                queue.append((pair[0], pair[1], w))
    raise WMethodUnknown("NONMINIMAL_HYPOTHESIS")


def characterization_set(machine):
    states = len(machine.transitions)
    witnesses = {""}
    for left in range(states):
        for right in range(left + 1, states):
            witnesses.add(separating_word(machine, left, right))
    return tuple(sorted(witnesses, key=lambda w: (len(w), w)))


@dataclass
class WMethodConformance:
    source: object  # Original RC39 SourceMeter, NEVER the reference graph.
    hidden_state_upper_bound: int
    verification_word_cap: int = 100000

    def __post_init__(self):
        if type(self.hidden_state_upper_bound) is not int or not 1 <= self.hidden_state_upper_bound <= 8:
            raise ValueError("invalid trusted bound")
        self.callbacks = 0
        self.total_words_checked = 0
        self.total_verified_symbols = 0
        self.certified_state_bound = None
        self.max_candidate_states = 0
        self.max_middle_length = 0
        self.cover_size = 0
        self.characterization_size = 0

    def seek_counterexample(self, candidate):
        """Discrepancy or complete bounded-state certificate, no graph peeking."""
        self.callbacks += 1
        if tuple(self.source.input_alphabet) != tuple(candidate.alphabet):
            raise WMethodUnknown("ALPHABET_MISMATCH")
        m = len(candidate.transitions)
        n = self.hidden_state_upper_bound
        self.max_candidate_states = max(self.max_candidate_states, m)
        if m > n:
            raise WMethodUnknown("CANDIDATE_EXCEEDS_TRUSTED_STATE_BOUND")
        access = state_cover(candidate)
        W = characterization_set(candidate)
        kmax = n - m
        self.max_middle_length = max(self.max_middle_length, kmax)
        cover = set(access)
        for prefix in access:
            for symbol in candidate.alphabet:
                cover.add(prefix + symbol)
        prefixes = tuple(sorted(cover, key=lambda w: (len(w), w)))
        self.cover_size = len(prefixes)
        self.characterization_size = len(W)
        tested = set()
        for prefix in prefixes:
            for length in range(kmax + 1):
                for symbols in product(candidate.alphabet, repeat=length):
                    middle = "".join(symbols)
                    for suffix in W:
                        word = prefix + middle + suffix
                        if word in tested:
                            continue
                        tested.add(word)
                        if self.total_words_checked >= self.verification_word_cap:
                            raise WMethodUnknown("W_SUITE_WORD_BUDGET_EXHAUSTED")
                        self.total_words_checked += 1
                        self.total_verified_symbols += len(word)
                        observed = self.source.membership(word)
                        if observed != candidate.run(word):
                            return word
        self.certified_state_bound = n
        return None
