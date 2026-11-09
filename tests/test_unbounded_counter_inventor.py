"""Q3 cross-language-class generalization: unknown unbounded state from I/O.

Scope: researcher-authored semantics, with independent-author original CFG/PDA
blind evaluation in a separate workflow. No hidden grammar rules provided.
"""
import random

from neumann1.unbounded_counter_inventor import (
    AdaptiveStateLanguageInventor,UnboundedCounterInventor)


def anbn(word):
    return int(
        not word or (len(word)%2==0 and
        word=="a"*(len(word)//2)+"b"*(len(word)//2)))


def dyck(word):
    total=0
    for c in word:
        total+=1 if c=="(" else -1
        if total<0:return 0
    return int(total==0)


def even_palindrome(word):
    return int(len(word)%2==0 and word==word[::-1])


def test_autonomous_class_switch_to_unbounded_counter_for_anbn():
    inventor=AdaptiveStateLanguageInventor(
        max_dfa_states=4,max_source_length=8)
    learned=inventor.invent(anbn,alphabet=("a","b"))
    assert learned.representation_class=="unbounded_counter",learned
    assert learned.finite_state_status!="SOURCE_CERTIFIED_CONDITIONAL_DFA"
    assert learned.program.ast[0]=="source_invented_unbounded_counter"
    for n in range(1,120):
        good="a"*n+"b"*n
        bad="a"*n+"b"*(n+1)
        assert learned.apply(good)==1
        assert learned.apply(bad)==0
        assert learned.apply(("ab")*n)==anbn(("ab")*n)
    rng=random.Random(94011)
    for n in (17,19,32,61,127,240):
        for _ in range(100):
            w="".join(rng.choice("ab") for _ in range(n))
            assert learned.apply(w)==anbn(w)


def test_same_inventor_synthesizes_balanced_nested_parenthesis_process():
    learned=AdaptiveStateLanguageInventor().invent(
        dyck,alphabet=("(",")"))
    assert learned.representation_class=="unbounded_counter",learned
    assert learned.program.require_nonnegative_prefix
    assert learned.program.forbidden_order is None
    for n in range(1,120):
        for word in ("("*n+")"*n,"()"*n,"(()())"*n,
                     ")"+"("*n+")"*n):
            assert learned.apply(word)==dyck(word)
    rng=random.Random(101010)
    for n in (19,33,68,131):
        for _ in range(100):
            w="".join(rng.choice("()") for _ in range(n))
            assert learned.apply(w)==dyck(w)


def test_counter_semantics_do_not_hallucinate_palindrome_grammar():
    learned=AdaptiveStateLanguageInventor().invent(
        even_palindrome,alphabet=("a","b"))
    assert learned.program is None
    assert learned.status=="ABSTAIN_NO_REPRESENTABLE_CLASS"


def test_dfa_class_retained_when_source_evidence_supports_it():
    regular=lambda w:int(w.count("a")%2==0)
    learned=AdaptiveStateLanguageInventor().invent(
        regular,alphabet=("a","b"))
    assert learned.representation_class=="finite_state"
    assert learned.program is not None
    for w in ("ab"*80,"a"*171+"b"*40,"b"*210):
        assert learned.apply(w)==regular(w)


def test_forbidden_target_probe_never_reaches_source_oracle():
    called=[]
    def oracle(w):
        assert w!="a"
        called.append(w)
        return anbn(w)
    learned=UnboundedCounterInventor().invent(
        oracle,alphabet=("a","b"),forbidden_target_words=("a",))
    assert learned.status=="ABSTAIN_TARGET_OVERLAP"
    assert not called


def test_adversarial_delayed_exception_is_not_globally_proved():
    normal=anbn
    delayed=lambda w:1 if w=="a"*30 else normal(w)
    learned=UnboundedCounterInventor().invent(
        delayed,alphabet=("a","b"))
    assert learned.status=="SOURCE_VERIFIED_UNBOUNDED_COUNTER"
    assert learned.apply("a"*30)!=delayed("a"*30)
    assert "finite examples alone" in learned.program.conditional_proof
