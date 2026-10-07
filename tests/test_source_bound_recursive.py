from copy import deepcopy
import pytest

from neumann1.source_bound_recursive import source_binding, certify_source_summary, SourceBoundDagEngine, ProtocolError
from neumann1.recursive_library_baseline import propose


SOURCE = """
type 'a clist = CNil | Single of 'a | Concat of 'a clist * 'a clist
type 'a list = Nil | Cons of 'a * 'a list
let rec sum = function
| Nil -> 0
| Cons (hd, tl) -> hd + sum tl
;;
let rec target = function
| CNil -> [%synt e]
| Single a -> [%synt leaf] a
| Concat (x, y) -> [%synt join] (target x) (target y)
;;
let rec repr t = c t
and c = function
| CNil -> Nil
| Single a -> Cons (a, Nil)
| Concat (x, y) -> dec y x
and dec l = function
| CNil -> repr l
| Single a -> Cons (a, repr l)
| Concat (x, y) -> dec (Concat (y, l)) x
;;
assert (target = repr @@ sum)
"""


def test_bound_assertion_and_termination():
    result = source_binding(SOURCE)
    assert result['assertion']['reference'] == 'sum'
    assert result['flatten_proof']['accepted']
    assert result['flatten_proof']['specifications']['dec'] == [1, 0]
    assert all(r['termination_status'] == 'unsat' for r in result['flatten_proof']['proof_records'])


def test_native_summary_can_fill_original_same_width_holes():
    public = source_binding(SOURCE)['projection']['public']
    result = certify_source_summary(SOURCE, propose(public)['proposal'])
    assert result['accepted'] and result['original_hole_skeleton_implementable']
    assert not result['machine_OCaml_execution_certified']


@pytest.mark.parametrize('before,after', [
    ('dec y x', 'dec x y'),
    ('Concat (y, l)', 'Concat (l, y)'),
    ('Cons (a, repr l)', 'repr l'),
    ('Cons (a, Nil)', 'Nil'),
    ('dec (Concat (y, l)) x', 'dec l (Concat (x, y))'),
    ('let rec repr t = c t', 'let rec repr t = repr t'),
    ('(target x) (target y)', '(target y) (target x)'),
    ('[@@', '[@@'),
])
def test_false_order_omission_cycle_and_target_rejected(before, after):
    if before == '[@@':
        changed = SOURCE+'\nassert (target = repr @@ sum)\n'
    else: changed = SOURCE.replace(before, after)
    with pytest.raises(ProtocolError): source_binding(changed)


def test_selected_helper_must_be_asserted_goal():
    with pytest.raises(ProtocolError): source_binding(SOURCE.replace('@@ sum', '@@ missing'))


def test_attribute_is_not_proof_and_pure_reference_still_required():
    changed = SOURCE.replace(';;\nlet rec target', '[@@ensures fun x -> x >= 0]\n;;\nlet rec target')
    assert source_binding(changed)['flatten_proof']['accepted']
    with pytest.raises(ValueError): source_binding(changed.replace('hd + sum tl', 'unknown hd (sum tl)'))


def test_false_candidate_cannot_get_source_goal_certificate():
    public = source_binding(SOURCE)['projection']['public']
    proposal = deepcopy(propose(public)['proposal'])
    proposal['decode']['outputs'] = [0]
    assert not certify_source_summary(SOURCE, proposal)['accepted']


def test_extra_state_does_not_claim_original_skeleton():
    changed = SOURCE.replace('sum = function','sum = function').replace('hd + sum tl', 'max 0 (hd + sum tl)')
    public = source_binding(changed)['projection']['public']
    proposal = propose(public)['proposal']
    result = certify_source_summary(changed, proposal)
    assert result['accepted'] and result['requires_added_or_changed_internal_state']
    assert not result['original_hole_skeleton_implementable']


def test_source_bound_dag_engine_and_certificate_copy():
    public=source_binding(SOURCE)['projection']['public']
    engine=SourceBoundDagEngine(SOURCE,propose(public)['proposal'])
    certificate=engine.certificate
    certificate['binding']['assertion']['reference']='wrong'
    result=engine.run({'semantics':'ordered_integer_list_dag','nodes':[['single',7],['single',-3],['concat',0,1],['concat',2,2]],'roots':[3]})
    assert result['outputs']==[[8]] and result['source_assertion']['reference']=='sum'
    engine._certificate['binding']['assertion']['reference']='wrong'
    with pytest.raises(ProtocolError):engine.run({'semantics':'ordered_integer_list_dag','nodes':[['nil']],'roots':[0]})


@pytest.mark.parametrize('injected', ['let max x y = 0\n', 'let rec max x y = 0\n', 'open Fake\n', 'external min : int -> int -> int = "wrong"\n'])
def test_primitive_shadowing_and_environment_changes_rejected(injected):
    with pytest.raises(ProtocolError):source_binding(injected+SOURCE)


def test_constructor_type_change_rejected():
    with pytest.raises(ProtocolError):source_binding(SOURCE.replace("Single of 'a", "Single of int * 'a"))


def test_local_reference_shadowing_rejected():
    with pytest.raises(ProtocolError):source_binding(SOURCE.replace('hd + sum tl','let sum = 0 in hd + sum tl'))


def test_indented_top_level_shadowing_rejected():
    with pytest.raises(ProtocolError):source_binding('  let max x y = 0\n'+SOURCE)


def test_rec_spacing_and_names_do_not_determine_binding():
    changed=SOURCE.replace('let rec','let  rec').replace('sum','renamed_reference').replace('repr','renamed_converter').replace('dec','continuation_helper')
    assert source_binding(changed)['flatten_proof']['accepted']
