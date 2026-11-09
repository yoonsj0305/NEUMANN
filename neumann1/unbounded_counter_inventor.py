"""Q3: discover a NEW unbounded integer-state language from SOURCE membership.

Unlike the finite-state inventor, the learned executable operator maintains an
integer whose magnitude can grow with input length, plus optional causal
prefix/order invariants. The executable program AST is inferred from source
membership evidence. No target outputs or author CFG/PDA rules enter search.

This is a bounded, human-supplied counter/metagrammar and classical enumerative
synthesis, NOT automatic invention of all nonregular languages. Finite SOURCE
observations cannot certify the correct hypothesis class.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from random import Random
from time import perf_counter_ns


class NoCounterRepresentation(ValueError):
    pass


def _words(alphabet, limit):
    yield ""
    for size in range(1, limit+1):
        for letters in product(alphabet,repeat=size):
            yield "".join(letters)


@dataclass(frozen=True)
class InventedCounterOperator:
    alphabet: tuple[str,str]
    weights: tuple[int,int]
    require_nonnegative_prefix: bool
    forbidden_order: tuple[str,str] | None
    source_examples: int
    source_verifiers: int
    candidates_checked: int
    source_queries: int
    source_horizon: int

    @property
    def ast(self):
        return (
            "source_invented_unbounded_counter",
            ("learned_counter_weights",self.weights),
            ("learned_prefix_invariant",self.require_nonnegative_prefix),
            ("learned_order_constraint",self.forbidden_order),
            ("learned_final_invariant","counter_equals_zero"),
        )

    @property
    def conditional_proof(self):
        return (
            "For all words, the compiled integer register equals the "
            "sum of learned character weights by induction. A state bound "
            "independent of input length is NOT assumed. The acceptance "
            "semantics are exact only if the black-box source belongs to "
            "this counter/invariant grammar; finite examples alone do not "
            "certify that hypothesis."
        )

    def apply(self,word):
        if type(word) is not str:
            raise TypeError("symbolic word required")
        weight=dict(zip(self.alphabet,self.weights))
        total=0
        observed=set()
        for c in word:
            if c not in weight:
                raise NoCounterRepresentation("symbol not in SOURCE alphabet")
            total+=weight[c]
            if self.require_nonnegative_prefix and total<0:
                return 0
            if self.forbidden_order is not None:
                previous,later=self.forbidden_order
                if c==later and previous in observed:
                    return 0
            observed.add(c)
        return int(total==0)


@dataclass(frozen=True)
class CounterDiscovery:
    status: str
    program: InventedCounterOperator | None
    source_queries: int
    candidate_count: int
    source_counterexamples: int
    elapsed_ms: float

    def apply(self,word):
        if self.program is None:
            raise NoCounterRepresentation(self.status)
        return self.program.apply(word)


class UnboundedCounterInventor:
    """Synthesize novel open-ended state transitions via SOURCE-only CEGIS."""

    def __init__(self,*,max_source_length=8,verification_queries=256,
                 max_queries=2000,max_source_ms=20000):
        if (type(max_source_length) is not int or
                not 4<=max_source_length<=12 or
                type(verification_queries) is not int or
                not 1<=verification_queries<=10000 or
                type(max_queries) is not int or
                not 1<=max_queries<=100000 or
                type(max_source_ms) not in (int,float) or
                not 1<=max_source_ms<=120000):
            raise ValueError("bounded source discovery budget")
        self.max_source_length=max_source_length
        self.verification_queries=verification_queries
        self.max_queries=max_queries
        self.max_source_ms=max_source_ms

    def invent(self,source_membership,*,alphabet=("a","b"),
               forbidden_target_words=(),known_classical=None):
        start=perf_counter_ns()
        alphabet=tuple(alphabet)
        if (len(alphabet)!=2 or
                any(type(x) is not str or len(x)!=1 for x in alphabet) or
                alphabet[0]==alphabet[1] or
                not callable(source_membership)):
            raise ValueError("two typed distinct source symbols required")
        forbidden=set(forbidden_target_words)
        train=tuple(_words(alphabet,self.max_source_length))
        # Independent SOURCE split of length greater than the training range,
        # includes both positive and negative lengths; no target gold.
        rng=Random(714213)
        probes=set()
        for j in range(self.verification_queries):
            size=self.max_source_length+1+(j%6)
            # deterministic length/word variety independent of source labels
            probe="".join(rng.choice(alphabet) for _ in range(size))
            probes.add(probe)
        extra=tuple(sorted(probes,key=lambda w:(len(w),w)))
        inputs=train+extra
        if len(inputs)>self.max_queries:
            return CounterDiscovery("ABSTAIN_QUERY_BUDGET",None,0,0,0,
                                    (perf_counter_ns()-start)/1e6)
        if any(w in forbidden for w in inputs):
            return CounterDiscovery("ABSTAIN_TARGET_OVERLAP",None,0,0,0,
                                    (perf_counter_ns()-start)/1e6)
        deadline=start+int(self.max_source_ms*1e6)
        observed={}
        try:
            for w in inputs:
                if perf_counter_ns()>deadline:
                    raise NoCounterRepresentation("ABSTAIN_SOURCE_TIME")
                label=source_membership(w)
                if type(label) is not int or label not in (0,1):
                    raise NoCounterRepresentation("ABSTAIN_SOURCE_NONBINARY")
                observed[w]=label
        except NoCounterRepresentation as e:
            return CounterDiscovery(str(e),None,len(observed),0,0,
                                    (perf_counter_ns()-start)/1e6)
        except (ValueError,TypeError,KeyError,OverflowError):
            return CounterDiscovery("ABSTAIN_SOURCE_ORACLE",None,len(observed),
                                    0,0,(perf_counter_ns()-start)/1e6)
        candidates=0
        counterexamples=0
        # Grammar atoms are count increments/decrements, a running-prefix
        # inequality and one learned pairwise temporal order relation.
        # There is NO supplied complete equality/order program.
        for weights,check_prefix,order in product(
                ((1,-1),(-1,1)),
                (False,True),
                (None,(alphabet[0],alphabet[1]),
                 (alphabet[1],alphabet[0]))):
            candidates+=1
            program=InventedCounterOperator(
                alphabet,weights,check_prefix,order,
                len(train),len(extra),candidates,len(observed),
                self.max_source_length+6)
            if any(program.apply(x)!=observed[x] for x in train):
                counterexamples+=1
                continue
            if any(program.apply(x)!=observed[x] for x in extra):
                counterexamples+=1
                continue
            if known_classical is not None and all(
                    known_classical(x)==observed[x] for x in inputs):
                return CounterDiscovery(
                    "CLASSICAL_FIRST",None,len(observed),candidates,
                    counterexamples,(perf_counter_ns()-start)/1e6)
            return CounterDiscovery(
                "SOURCE_VERIFIED_UNBOUNDED_COUNTER",program,
                len(observed),candidates,counterexamples,
                (perf_counter_ns()-start)/1e6)
        return CounterDiscovery(
            "ABSTAIN_OUTSIDE_COUNTER_LANGUAGE",None,len(observed),
            candidates,counterexamples,
            (perf_counter_ns()-start)/1e6)


@dataclass(frozen=True)
class AdaptiveSemanticDiscovery:
    status: str
    representation_class: str
    program: object | None
    finite_state_status: str
    counter_status: str
    source_calls: int

    def apply(self,word):
        if self.program is None:
            raise NoCounterRepresentation(self.status)
        return self.program.apply(word)


class AdaptiveStateLanguageInventor:
    """Falsify a too-small finite-state representation, then invent counter state.

    This is a two-class human-given metalanguage switch based on SOURCE
    evidence, not a general ontology-discovery proof.
    """

    def __init__(self,*,max_dfa_states=4,max_source_length=8):
        self.max_dfa_states=max_dfa_states
        self.max_source_length=max_source_length

    def invent(self,source_membership,*,alphabet,
               forbidden_target_words=()):
        from .unknown_state_operator_inventor import (
            UnknownStateOperatorInventor)
        alphabet=tuple(alphabet)
        source_calls=0
        def oracle(w):
            nonlocal source_calls
            source_calls+=1
            return source_membership(w)
        # Independent SOURCE probes of longer words for falsifying the
        # conditional finite-state hypothesis.
        rng=Random(78431)
        verification_words=set("".join(
            rng.choice(alphabet)
            for _ in range(2*self.max_dfa_states+2+j%5))
            for j in range(160))
        # Generic symmetry/order probes, generated without task labels.
        # These are important for falsifying a spurious bounded DFA on
        # rare positive, long structured words; random words alone can be
        # almost entirely negative on many nonregular languages.
        a,b=alphabet
        for n in range(self.max_dfa_states,9):
            verification_words.update((
                a*n+b*n,b*n+a*n,(a+b)*n,(b+a)*n,
                a*n+b*n+a*n+b*n,b*n+a*n+b*n+a*n))
        verification_words={
            w for w in verification_words if len(w)>2*self.max_dfa_states-1}
        long_checks=tuple(
            (w,oracle(w)) for w in sorted(
                verification_words,key=lambda w:(len(w),w)))
        finite=UnknownStateOperatorInventor(
            max_states=self.max_dfa_states,max_queries=25000).invent(
            oracle,alphabet=alphabet,
            independent_source_checks=long_checks,
            forbidden_target_words=forbidden_target_words)
        if finite.program is not None:
            return AdaptiveSemanticDiscovery(
                "SOURCE_VERIFIED_FINITE_STATE","finite_state",
                finite.program,finite.status,"NOT_ATTEMPTED",source_calls)
        unbounded=UnboundedCounterInventor(
            max_source_length=self.max_source_length).invent(
            oracle,alphabet=alphabet,
            forbidden_target_words=forbidden_target_words)
        if unbounded.program is not None:
            return AdaptiveSemanticDiscovery(
                "SOURCE_VERIFIED_UNBOUNDED_COUNTER","unbounded_counter",
                unbounded.program,finite.status,unbounded.status,source_calls)
        return AdaptiveSemanticDiscovery(
            "ABSTAIN_NO_REPRESENTABLE_CLASS","none",None,
            finite.status,unbounded.status,source_calls)
