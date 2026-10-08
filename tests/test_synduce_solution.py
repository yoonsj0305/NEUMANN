from copy import deepcopy
from itertools import product
import pytest

from neumann1.recursive_summary import SummaryError, interpret, program, reference
from neumann1.synduce_solution import (parse_solution, certify_solution,
                                      singleton_binding, run_raw_kernel)


SUM = '''let s0 = 0
let f0 a = a
let j0 l r = l + r
let rec h = function
| CNil -> s0
| Single(a) -> f0 a
| Concat(l, r) -> j0 (h l) (h r)
'''

PREFIX = '''let s0 = (0,0)
let f0 a = (max a 0,a)
let j0 (lp,ls) (rp,rs) = (max lp (ls + rp), ls + rs)
let rec h = function
| CNil -> s0
| Single(a) -> f0 a
| Concat(l, r) -> j0 (h l) (h r)
'''


def p(empty, outputs):
    return {'semantics': 'integer_list_right_fold', 'empty': empty,
            'step': program(['head'] + [f'r{i}' for i in range(len(empty))], outputs)}


def tree(xs):
    if not xs:return ['nil']
    return ['concat', ['single', xs[0]], tree(xs[1:])]


def test_raw_constructor_binding_and_sum_certification():
    public = p([0], [['add', 'head', 'r0']])
    result = certify_solution(public, SUM)
    assert result['accepted'] and len(result['attempts'][0]['certificate']['obligations']) == 9
    assert result['singleton_binding']['status'] == 'unsat'
    for xs in [[], [10**80, -10**80, 7], [-2, 4, 9]]:
        assert run_raw_kernel(result['kernel'], tree(xs)) == reference(public, xs)


def test_lifted_emitted_prefix_preserves_original_scalar_goal():
    public = p([0], [['max', ['add', 'head', 'r0'], 0]])
    result = certify_solution(public, PREFIX)
    assert result['accepted'] and result['attempts'][-1]['decode_indices'] == [0]
    assert len(result['proposal']['empty']) == 2
    for length in range(5):
        for xs in product([-2, 0, 3], repeat=length):
            state = run_raw_kernel(result['kernel'], tree(list(xs)))
            assert interpret(result['proposal']['decode'], state) == reference(public, list(xs))


def test_false_sum_solution_is_refuted_against_public_spec():
    result = certify_solution(p([0], [['add', 'head', 'r0']]), SUM.replace('let f0 a = a', 'let f0 a = 0'))
    assert not result['accepted']
    assert any(a['certificate']['status'] == 'REFUTED' for a in result['attempts'])


def test_actual_singleton_binding_is_separate_from_summary_conditions():
    kernel = parse_solution(SUM)
    kernel['singleton']['outputs'] = [['add', 'head', 1]]
    checked = singleton_binding(kernel)
    assert not checked['accepted'] and checked['status'] == 'sat'


@pytest.mark.parametrize('source', [
    SUM.replace('(h l) (h r)', '(h r) (h l)'),
    SUM.replace('l + r', 'l * r'),
    SUM.replace('let f0 a = a', 'let f0 a = evil a'),
    SUM.replace('let rec h = function', 'let rec h parameter = function'),
    SUM.replace('CNil -> s0', 'Other -> s0'),
    SUM.replace('Single(a) -> f0 a', 'Single(a) -> f0 b'),
    SUM.replace('let s0 = 0', 'let s0 = true'),
])
def test_unsupported_source_never_executes(source):
    with pytest.raises(SummaryError):parse_solution(source)


def test_constructor_budgets_and_malformed_tree_reject():
    kernel = parse_solution(SUM)
    for t in [['single', True], ['concat', ['nil']], ['unknown']]:
        with pytest.raises(SummaryError):run_raw_kernel(kernel, t)
    with pytest.raises(SummaryError):run_raw_kernel(kernel, tree([1,2]), max_nodes=2)
    with pytest.raises(SummaryError):certify_solution(p([0], ['r0']), SUM, max_decoders=0)
