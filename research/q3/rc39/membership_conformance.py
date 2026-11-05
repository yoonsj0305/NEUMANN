"""RC39 source-membership-only all-length conformance without a gold EQ oracle.

The learner may request observed outputs of chosen words. A finite
conformance tester searches for a counterexample solely by these same
membership observations. It uses a PUBLIC upper bound on the number of
unknown target states, not the hidden target transition graph.

The exhaustive length bound is conservative: If two deterministic
complete Mealy machines have n,m states and differ, the two initial states
in their disjoint union have a distinguishing continuation of length
at most n+m-1 (iterated partition refinement). Thus checking all words
up to MAX_REFERENCE_STATES + compiled_states - 1 is exact within this
finite-state model class. Exponential membership cost is fully charged.
"""
from __future__ import annotations
from itertools import product
from dataclasses import dataclass
from time import process_time_ns
from typing import Callable

from research.q3.rc39.active_mealy import MealyProgram,UnknownStateStructure

@dataclass
class SourceMeter:
    backend: Callable[[str],str]
    input_alphabet: str
    output_alphabet: str
    query_cap: int=100000

    def __post_init__(self):
        self.cache:dict[str,str]={}
        self.unique_queries=0
        self.unique_query_symbols=0
        self.requested_queries=0
        self.requested_symbols=0

    def membership(self,word:str)->str:
        if type(word)!=str or any(c not in self.input_alphabet for c in word):
            raise UnknownStateStructure("INVALID_SOURCE_INPUT")
        self.requested_queries+=1
        self.requested_symbols+=len(word)
        if word not in self.cache:
            if self.unique_queries>=self.query_cap:
                raise UnknownStateStructure("TOTAL_SOURCE_MEMBERSHIP_BUDGET_EXHAUSTED")
            result=self.backend(word)
            if type(result)!=str or len(result)!=len(word) or any(c not in self.output_alphabet for c in result):
                raise UnknownStateStructure("INVALID_SOURCE_RESPONSE")
            self.cache[word]=result
            self.unique_queries+=1
            self.unique_query_symbols+=len(word)
        return self.cache[word]

@dataclass
class MembershipConformance:
    source:SourceMeter
    hidden_state_upper_bound:int
    verification_word_cap:int=100000

    def __post_init__(self):
        if type(self.hidden_state_upper_bound)!=int or not 1<=self.hidden_state_upper_bound<=8:
            raise ValueError("invalid advertised bound")
        self.callbacks=0
        self.total_words_checked=0
        self.total_verified_symbols=0
        self.certified_max_word_length=None
        self.max_guessed_states=0

    def seek_counterexample(self,candidate:MealyProgram):
        """Callback compatible with active learner but contains NO gold graph."""
        self.callbacks+=1
        m=len(candidate.transitions)
        self.max_guessed_states=max(self.max_guessed_states,m)
        cutoff=self.hidden_state_upper_bound+m-1
        if cutoff<1:raise UnknownStateStructure("NEGATIVE_COMPLETENESS_LENGTH")
        for length in range(cutoff+1):
            for chars in product(self.source.input_alphabet,repeat=length):
                if self.total_words_checked>=self.verification_word_cap:
                    raise UnknownStateStructure("CONFORMANCE_WORD_BUDGET_EXHAUSTED")
                w="".join(chars)
                self.total_words_checked+=1
                self.total_verified_symbols+=len(w)
                observed=self.source.membership(w)
                if candidate.run(w)!=observed:
                    return w
        self.certified_max_word_length=cutoff
        return None

def compare_source_rights(learner,reference_backend,*,upper_bound=5,
                          source_cap=100000,conformance_cap=100000):
    started=process_time_ns()
    meter=SourceMeter(reference_backend,"ABC","01",source_cap)
    conformance=MembershipConformance(meter,upper_bound,conformance_cap)
    try:
        result=learner.learn(meter.membership,conformance.seek_counterexample)
        reason=result.status
    except UnknownStateStructure as exc:
        result=None
        reason="UNKNOWN:"+str(exc)
    return {
      "status":reason,
      "model_source":result.source if result else None,
      "learner_membership_calls":result.membership_calls if result else None,
      "learner_equivalence_callback_calls":result.equivalence_calls if result else None,
      "total_unique_source_membership_calls":meter.unique_queries,
      "total_unique_source_symbols":meter.unique_query_symbols,
      "all_source_query_requests_including_cached":meter.requested_queries,
      "all_requested_word_symbols_including_cached":meter.requested_symbols,
      "conformance_callbacks":conformance.callbacks,
      "conformance_full_word_checks":conformance.total_words_checked,
      "conformance_total_word_symbols":conformance.total_verified_symbols,
      "completed_completeness_cutoff":conformance.certified_max_word_length,
      "maximum_candidate_state_count":conformance.max_guessed_states,
      "total_process_cpu_ms":(process_time_ns()-started)/1e6,
      "learner_process_cpu_ms":result.process_cpu_ms if result else None,
      "oracle_access":"membership_only; unknown model graph never passed to learner or conformance"
    }
