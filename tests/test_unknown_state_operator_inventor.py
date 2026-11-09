"""Q3 new invented STATE representation, not a supplied transition table.

Researcher-created unit/formal examples. Independently authored originals
are a separate gate, not implied by green unit tests.
"""
from itertools import product
from random import Random

from neumann1.unknown_state_operator_inventor import (
    UnknownStateOperatorInventor, MissingStateEvidence)


def words(alphabet, maximum):
    for n in range(maximum+1):
        for tup in product(alphabet, repeat=n):
            yield "".join(tup)


def test_hidden_four_state_parity_automaton_and_new_length_generalization():
    oracle=lambda word:int(word.count("a") % 2 == 1 and
                           word.count("b") % 2 == 1)
    checks=tuple((w,oracle(w)) for w in (
        "aaaabababa","ababababaabb","bbbbaaaaaaba","aaaaabbbaaaa"))
    result=UnknownStateOperatorInventor(max_states=4).invent(
        oracle,alphabet=("a","b"),independent_source_checks=checks)
    assert result.status=="SOURCE_CERTIFIED_CONDITIONAL_DFA",result
    assert result.program.state_count==4
    assert result.program.ast[0]=="source_invented_latent_finite_state_operator"
    assert result.program.source_queries<=255
    for word in words(("a","b"),10):
        assert result.apply(word)==oracle(word)
    rng=Random(102204)
    for n in (70,129,513,1001):
        for _ in range(20):
            word="".join(rng.choice("ab") for _ in range(n))
            assert result.apply(word)==oracle(word)
            assert len(result.program.state_trace(word))==n+1


def test_discovers_numeric_modular_operator_from_raw_binary_symbols():
    # No modular arithmetic instruction or integer-conversion operation
    # exists in the learned automaton's language. The modulo states and
    # transition table are inferred solely from word membership responses.
    oracle=lambda w:int(int(w or "0",2)%5==0)
    checks=tuple((w,oracle(w)) for w in (
        "110010101","10111100001","100000000000","111011100010"))
    result=UnknownStateOperatorInventor(max_states=5).invent(
        oracle,alphabet=("0","1"),independent_source_checks=checks)
    assert result.status=="SOURCE_CERTIFIED_CONDITIONAL_DFA",result
    assert result.program.state_count==5
    for x in range(8000):
        word=format(x,"b")
        assert result.apply(word)==int(x%5==0)


def test_unknown_state_discovery_is_not_a_fixed_regex_solver():
    # Third independent meaning: consecutive "ba" signal in protocol log.
    oracle=lambda w:int("ba" in w)
    checks=(("aaabba",1),("bbbbab",1),("aaabb",0))
    result=UnknownStateOperatorInventor(max_states=3).invent(
        oracle,alphabet=("a","b"),independent_source_checks=checks)
    assert result.status=="SOURCE_CERTIFIED_CONDITIONAL_DFA",result
    assert result.program.state_count==3
    for w in words(("a","b"),11):
        assert result.apply(w)==oracle(w)


def test_full_exhaustive_all_binary_three_state_transition_semantics():
    # 3^(3*2) transition tables * 2^3 acceptance assignments = 5832
    # differently encoded SOURCE functions. No hidden state information is
    # passed to the learner, only membership oracle labels.
    n=3
    checked=0
    for transition_digits in product(range(n),repeat=n*2):
        transitions=(
            transition_digits[:2],transition_digits[2:4],
            transition_digits[4:6])
        for accept_bits in product((0,1),repeat=n):
            def oracle(w):
                state=0
                for c in w:
                    state=transitions[state][c=="1"]
                return accept_bits[state]
            learned=UnknownStateOperatorInventor(
                max_states=n,max_queries=63).invent(oracle)
            assert learned.status=="SOURCE_CERTIFIED_CONDITIONAL_DFA"
            for word in ("1010110100110110","0"*61+"1","1"*50+"0",
                         "1010"*31):
                assert learned.apply(word)==oracle(word)
                checked+=1
    assert checked==(3**6)*(2**3)*4


def test_known_classical_preempts_zero_invention_queries():
    requested=[]
    def oracle(w):
        requested.append(w)
        return int(w.endswith("01"))
    check=(("001",1),("111",0),("101",1))
    result=UnknownStateOperatorInventor(max_states=4).invent(
        oracle,independent_source_checks=check,
        known_classical=lambda w:int(w.endswith("01")))
    assert result.status=="CLASSICAL_FIRST"
    assert result.program is None
    assert result.queried_source_words==0
    assert not requested


def test_falsifiable_and_forbidden_interfaces_abstain():
    oracle=lambda w:int(w=="1"*11)
    engine=UnknownStateOperatorInventor(max_states=3)
    blocked=engine.invent(oracle,forbidden_target_words=("1",))
    assert blocked.status=="ABSTAIN_TARGET_OVERLAP"
    assert blocked.queried_source_words==0
    invalid=engine.invent(lambda w:2)
    assert invalid.status=="ABSTAIN_NONBINARY_SOURCE"
    # A source verifier on a length longer than all identification queries
    # can reveal a bounded-class violation, so the engine must ABSTAIN.
    falsified=engine.invent(
        oracle, independent_source_checks=(("1"*11,1),))
    assert falsified.status=="ABSTAIN_SOURCE_COUNTEREXAMPLE"


def test_no_unrestricted_identifiability_from_finite_automaton_probes():
    # The conditional DFA bound cannot itself be inferred from this oracle.
    # A delayed one-off exceptional input of length 11 is indistinguishable
    # from reject-all on the N=3 membership basis (length <=5).
    delayed=lambda w:int(w=="1"*11)
    learned=UnknownStateOperatorInventor(max_states=3).invent(delayed)
    assert learned.status=="SOURCE_CERTIFIED_CONDITIONAL_DFA"
    assert learned.apply("1"*11)==0
    assert delayed("1"*11)==1
    assert "CONDITIONAL" in learned.program.conditional_proof.upper()
