"""Bounded-state, source-membership-only W-method conformance for RC39.

Classical W-method, NOT a newly invented learning algorithm. Given a trusted
bound N on the hidden COMPLETE deterministic Mealy machine's reachable states,
construct a k-complete test suite from the MINIMAL candidate hypothesis H:

    T = P · Sigma^{<= N-|H|+1} · W

P: shortest state cover, W: candidate state-characterization set. Every
source test is charged to SourceMeter, and exhaustion returns UNKNOWN.
No hidden graph, reference state count, or direct equivalence oracle is read.

Correctness scope: deterministic complete Mealy, reset for each membership
query, truthful oracle, same finite alphabet, trusted state bound. Unbounded
systems and invalid bounds are NOT certified. See TACAS 2024 'Small Test
Suites for Active Automata Learning' for classical W-method prerequisites.
"""
from __future__ import annotations

from collections import deque
from itertools import product
from time import process_time_ns

from research.q3.rc39.active_mealy import MealyProgram, UnknownStateStructure
from research.q3.rc39.membership_conformance import SourceMeter


def _reachable_access(machine: MealyProgram) -> dict[int, str]:
    access = {machine.initial: ""}
    queue = deque([machine.initial])
    while queue:
        state = queue.popleft()
        for idx, letter in enumerate(machine.alphabet):
            nxt = machine.transitions[state][idx]
            if nxt not in access:
                access[nxt] = access[state] + letter
                queue.append(nxt)
    return access


def minimal_hypothesis(candidate: MealyProgram) -> MealyProgram:
    """Discard unreachable states and merge behavior-equivalent states.

    Synchronous finite partition refinement; no target/source observations.
    The W-method's k parameter must use the number of MINIMAL states.
    """
    candidate = MealyProgram.from_source(candidate.to_source())
    access = _reachable_access(candidate)
    reachable = tuple(access)
    # A state is initially characterized by its one-letter emissions.
    groups = {}
    part = {}
    for s in reachable:
        signature = candidate.emissions[s]
        if signature not in groups:
            groups[signature] = len(groups)
        part[s] = groups[signature]
    for _ in range(len(reachable) + 1):
        groups = {}
        new_part = {}
        for s in reachable:
            signature = (candidate.emissions[s],
                         tuple(part[candidate.transitions[s][a]]
                               for a in range(len(candidate.alphabet))))
            if signature not in groups:
                groups[signature] = len(groups)
            new_part[s] = groups[signature]
        if new_part == part:
            break
        part = new_part
    else:
        raise UnknownStateStructure("MINIMIZATION_FAILED")
    representatives = {}
    for s in reachable:
        representatives.setdefault(part[s], s)
    transitions = []
    emissions = []
    for i in range(len(representatives)):
        s = representatives[i]
        transitions.append(tuple(part[t] for t in candidate.transitions[s]))
        emissions.append(candidate.emissions[s])
    result = MealyProgram(candidate.alphabet, candidate.outputs,
                          tuple(transitions), tuple(emissions),
                          part[candidate.initial])
    return MealyProgram.from_source(result.to_source())


def _from_state(machine: MealyProgram, state: int, word: str) -> str:
    output = []
    for letter in word:
        idx = machine.alphabet.index(letter)
        output.append(machine.emissions[state][idx])
        state = machine.transitions[state][idx]
    return "".join(output)


def _shortest_distinguishing_suffix(machine: MealyProgram, i: int, j: int) -> str:
    work = deque([(i, j, "")])
    seen = {(i, j)}
    while work:
        left, right, prefix = work.popleft()
        for a, letter in enumerate(machine.alphabet):
            if machine.emissions[left][a] != machine.emissions[right][a]:
                return prefix + letter
            nxt = (machine.transitions[left][a], machine.transitions[right][a])
            if nxt not in seen:
                seen.add(nxt)
                work.append((nxt[0], nxt[1], prefix + letter))
    raise UnknownStateStructure("CANDIDATE_NOT_MINIMAL")


def characterization_set(machine: MealyProgram) -> tuple[str, ...]:
    """Deterministically find a complete W; does not require minimal |W|."""
    count = len(machine.transitions)
    if count == 1:
        return (machine.alphabet[0],)  # W must be nonempty, even for one state
    witnesses = {
        _shortest_distinguishing_suffix(machine, i, j)
        for i in range(count) for j in range(i + 1, count)
    }
    # Optional exact set cover over a tiny <=16-state hypothesis not needed.
    result = tuple(sorted(witnesses, key=lambda w: (len(w), w)))
    for i in range(count):
        for j in range(i + 1, count):
            if not any(_from_state(machine, i, w) != _from_state(machine, j, w)
                       for w in result):
                raise UnknownStateStructure("INCOMPLETE_CHARACTERIZATION_SET")
    return result


class WMethodConformance:
    def __init__(self, source: SourceMeter, hidden_state_upper_bound: int,
                 verification_word_cap: int = 100000):
        if type(hidden_state_upper_bound) is not int or not (1 <= hidden_state_upper_bound <= 8):
            raise ValueError("invalid advertised reference bound")
        if type(verification_word_cap) is not int or verification_word_cap < 1:
            raise ValueError("invalid conformance budget")
        self.source = source
        self.hidden_state_upper_bound = hidden_state_upper_bound
        self.verification_word_cap = verification_word_cap
        self.callbacks = 0
        self.total_words_checked = 0
        self.total_verified_symbols = 0
        self.completed_certificates = 0
        self.last_candidate_min_states = None
        self.last_characterization_count = None
        self.max_infix_length = None

    def seek_counterexample(self, candidate: MealyProgram) -> str | None:
        self.callbacks += 1
        if tuple(self.source.input_alphabet) != candidate.alphabet:
            raise UnknownStateStructure("SOURCE_HYPOTHESIS_ALPHABET_MISMATCH")
        if not set(candidate.outputs).issubset(set(self.source.output_alphabet)):
            raise UnknownStateStructure("SOURCE_HYPOTHESIS_OUTPUT_MISMATCH")
        model = minimal_hypothesis(candidate)
        states = len(model.transitions)
        self.last_candidate_min_states = states
        if states > self.hidden_state_upper_bound:
            # A more complex hypothesis cannot be equivalent to a reference
            # with fewer than 'states' MINIMAL states. Must not return None.
            raise UnknownStateStructure("HYPOTHESIS_EXCEEDS_REFERENCE_STATE_BOUND")
        access = _reachable_access(model)
        w_set = characterization_set(model)
        max_infix = self.hidden_state_upper_bound - states + 1
        self.last_characterization_count = len(w_set)
        self.max_infix_length = max_infix
        words_seen = set()
        for prefix in access.values():
            for length in range(max_infix + 1):
                for symbols in product(model.alphabet, repeat=length):
                    infix = "".join(symbols)
                    for suffix in w_set:
                        word = prefix + infix + suffix
                        if word in words_seen:
                            continue
                        words_seen.add(word)
                        if self.total_words_checked >= self.verification_word_cap:
                            raise UnknownStateStructure("W_METHOD_WORD_BUDGET_EXHAUSTED")
                        self.total_words_checked += 1
                        self.total_verified_symbols += len(word)
                        observed = self.source.membership(word)
                        if model.run(word) != observed:
                            return word
        self.completed_certificates += 1
        return None


def compare_wmethod_source_rights(learner, reference_backend, *, upper_bound=5,
                                  source_cap=100000, conformance_cap=100000,
                                  alphabet="ABC", outputs="01"):
    began = process_time_ns()
    meter = SourceMeter(reference_backend, alphabet, outputs, source_cap)
    verifier = WMethodConformance(meter, upper_bound, conformance_cap)
    try:
        outcome = learner.learn(meter.membership, verifier.seek_counterexample)
        status = outcome.status
    except UnknownStateStructure as exc:
        outcome = None
        status = "UNKNOWN:" + str(exc)
    return {
        "status": status,
        "model_source": outcome.source if outcome else None,
        "learner_membership_calls": outcome.membership_calls if outcome else None,
        "learner_equivalence_callback_calls": outcome.equivalence_calls if outcome else None,
        "total_unique_source_membership_calls": meter.unique_queries,
        "total_unique_source_symbols": meter.unique_query_symbols,
        "all_source_query_requests_including_cached": meter.requested_queries,
        "all_requested_word_symbols_including_cached": meter.requested_symbols,
        "conformance_callbacks": verifier.callbacks,
        "conformance_full_word_checks": verifier.total_words_checked,
        "conformance_total_word_symbols": verifier.total_verified_symbols,
        "conformance_complete_certificates": verifier.completed_certificates,
        "last_minimal_hypothesis_states": verifier.last_candidate_min_states,
        "characterization_suffixes": verifier.last_characterization_count,
        "max_infix_length": verifier.max_infix_length,
        "total_process_cpu_ms": (process_time_ns()-began) / 1e6,
        "oracle_access": "membership_only; W-method candidate structure; trusted public <=N target bound",
        "wmethod_classical_not_neural": True,
    }
