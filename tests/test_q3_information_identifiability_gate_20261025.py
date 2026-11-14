"""Regression proof: a one-query Q3 oracle check may certify nothing globally."""
import itertools,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"))
from information_gate_20261025 import (UNKNOWN,CONDITIONAL,required_basis,evidence_status,
cubic_identification_lower_bound,balanced_attacker,leave_one_out_catches_two_cubic_terms,
hidden_unseen_2)

def test_prior_extra_query_is_not_a_universal_certificate():
    for n in (8,10):
        groups=((0,1),(2,3),(4,5))
        probes=list(required_basis(n,2))
        probes.append(tuple(range(n)))
        probes += [tuple(i for i in range(n) if i!=j) for j in range(n)]
        for q in probes:
            x=[int(i in q) for i in range(n)]
            assert balanced_attacker(x,groups)==0
        x=[int(i in (0,2,4)) for i in range(n)]
        assert balanced_attacker(x,groups)==1

def test_completeness_is_explicitly_class_conditional_not_global():
    for n in (8,10):
        assert evidence_status(n,list(required_basis(n,2))+[tuple(range(n))])==UNKNOWN
        assert evidence_status(n,required_basis(n,3))==CONDITIONAL
        assert "CERTIFIED" not in evidence_status(n,required_basis(n,3))
        assert cubic_identification_lower_bound(n)==(56 if n==8 else 120)

def test_two_cubic_cancellation_families_all_need_only_n_leave_one_out():
    for n in (8,10):
        terms=list(itertools.combinations(range(n),3))
        assert all(leave_one_out_catches_two_cubic_terms(n,a,b)
                   for a,b in itertools.combinations(terms,2))

def test_no_binary_only_observations_can_detect_unrestricted_hidden_point():
    for n in (8,10):
        assert all(hidden_unseen_2(x)==0 for x in itertools.product((0,1),repeat=n))
        assert hidden_unseen_2((2,)*n)==1

def test_triple_support_probes_form_full_rank_identity():
    for n in (8,10):
        for triple in itertools.combinations(range(n),3):
            x=[int(i in triple) for i in range(n)]
            detected=[a for a in itertools.combinations(range(n),3)
                       if x[a[0]]*x[a[1]]*x[a[2]]]
            assert detected==[triple]
