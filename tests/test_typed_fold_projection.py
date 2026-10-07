import itertools
import pytest

from neumann1.recursive_summary import SummaryError, reference, CertifiedSummary
from neumann1.typed_fold_projection import project
from neumann1.recursive_library_baseline import propose

MBO="""let rec mbo = function | Nil -> 0, 0, 0, true | Cons (hd, tl) ->
let cl, ml, c, conj = mbo tl in
let ncl = if hd then cl + 1 else 0 in
let nconj = conj && hd in
let nc = if nconj then c + 1 else c in
ncl, max ml ncl, nc, nconj ;;"""


def test_boolean_state_encoding_preserves_independent_run_length_definition():
    p=project(MBO)
    assert p['input_type']=='Bool' and p['goal_types']==['Int','Int','Int','Bool']
    for n in range(7):
        for bits in itertools.product([0,1],repeat=n):
            prefix=0
            for bit in bits:
                if not bit:break
                prefix+=1
            suffix=0
            for bit in reversed(bits):
                if not bit:break
                suffix+=1
            longest=max([len(block) for block in ''.join(map(str,bits)).split('0')],default=0)
            assert reference(p['public'],list(bits))==[prefix,longest,suffix,int(all(bits))]


def test_boolean_input_integer_encoding_is_explicit():
    p=project(MBO)
    assert reference(p['public'],[5,-9,12,0])==reference(p['public'],[1,0,1,0])
    assert p['Boolean_input_encoding']=='positive->true, nonpositive->false'


def test_known_boolean_run_monoid_is_certified_with_same_checker():
    from tests.test_recursive_library_baseline import tree
    public=project(MBO)['public']
    found=propose(public)
    assert found and found['template']=='boolean_run_lengths'
    engine=CertifiedSummary(public,found['proposal'])
    for bits in itertools.product([0,1],repeat=5):
        assert engine.run(tree(list(bits)))==reference(public,list(bits))


def test_local_let_scope_and_boolean_conditional_arms():
    source="""let rec f = function | Nil -> true | Cons (hd, tl) ->
    let x = f tl in if hd > 0 then x else false ;;"""
    p=project(source)
    assert p['input_type']=='Int'
    assert reference(p['public'],[])==[1]
    assert reference(p['public'],[3,2,1])==[1]
    assert reference(p['public'],[3,0,1])==[0]


def test_original_order_and_negative_abs_math_integer_semantics():
    source="""let rec f = function | Nil -> 0 | Cons (hd, tl) -> abs hd + f tl ;;"""
    p=project(source)
    assert reference(p['public'],[-2,3,-10**40])==[10**40+5]


@pytest.mark.parametrize('body',['hd * f tl','unknown tl','if hd then hd + 1 else 0',
                                'f hd','(f tl, 0)','if hd then true else 1'])
def test_unknown_effects_recursion_types_or_nonlinearity_reject(body):
    source='let rec f = function | Nil -> 0 | Cons (hd, tl) -> '+body+' ;;'
    with pytest.raises(SummaryError):project(source)


def test_assert_selects_declared_reference_instead_of_first_matching_helper():
    source="""let rec helper = function | Nil -> 0 | Cons(hd,tl) -> helper tl ;;
    let rec spec = function | Nil -> 0 | Cons(hd,tl) -> hd + spec tl ;;
    assert (target = repr @@ spec)"""
    p=project(source)
    assert p['reference_function']=='spec' and reference(p['public'],[3,4])==[7]
