import itertools
import pytest
from neumann1.functional_source import Data, SourceError, WorkLimit, parse, execute


SUM = r'''
Inductive List = nil Unit | cons {Int, List};
sum = fix (\f: List -> Int. \xs: List.
  match xs with nil _ -> 0 | cons {h,t} -> + h (f t) end);
main = \xs:List. sum xs;
'''


def linked(values):
    value = Data('nil', None)
    for item in reversed(values):
        value = Data('cons', (item, value))
    return value


def test_recursive_source_matches_arithmetic_on_signed_lists():
    source = parse(SUM)
    for size in range(5):
        for values in itertools.product([-3,0,2], repeat=size):
            assert execute(source, [linked(values)], signed_bits=32) == sum(values)


def test_lexical_binding_and_higher_order_closure_are_preserved():
    source = parse(r'''
    x = 7; f = \y:Int. + x y; x = 99;
    twice = \f:Int -> Int. \x:Int. f (f x);
    main = twice f 2;
    ''')
    assert execute(source) == 16


def test_pattern_binding_shadows_but_does_not_mutate_outer_environment():
    source = parse(r'''
    Inductive Tree = leaf Int | node {Tree,Tree};
    x = 5; walk = fix (\f:Tree -> Int. \x:Tree.
      match x with leaf x -> x | node {l,r} -> + (f l) (f r) end);
    main = + (walk (node {leaf 3,leaf -2})) x;
    ''')
    assert execute(source) == 6


def test_division_truncates_towards_zero_instead_of_python_floor():
    assert execute(parse('main = / -7 3;')) == -2
    assert execute(parse('main = / 7 -3;')) == -2
    with pytest.raises(SourceError, match='zero'):
        execute(parse('main = / 7 0;'))


def test_guarded_branch_is_lazy_and_boolean_operators_are_strict():
    assert execute(parse('main = if true then 7 else / 1 0;')) == 7
    with pytest.raises(SourceError, match='zero'):
        execute(parse('main = and false (== (/ 1 0) 0);'))


def test_tuple_projection_and_mutual_data_declarations():
    source = parse(r'''
    Inductive Tree = leaf Unit | node {Int,Forest}
      with Forest = empty Unit | join {Tree,Forest};
    pick = \t:Tree. match t with leaf _ -> 0 | node {x,_} -> x end;
    main = {pick (node {4,empty unit}), true}.1;
    ''')
    assert execute(source) == 4
    with pytest.raises(SourceError, match='projection'):
        execute(parse('main = {1,2}.3;'))


def test_explicit_input_is_bound_before_functions_capture_it():
    source = parse(r'@Input x:Int; f = \y:Int. + x y; @Start main = f 2;')
    assert execute(source, inputs={'x': 8}) == 10
    with pytest.raises(SourceError, match='Input bindings'):
        execute(source)
    with pytest.raises(SourceError, match='Input bindings'):
        execute(source, inputs={'x':8,'extra':9})


def test_marks_are_explicitly_erased_and_comments_do_not_change_tokens():
    source = parse(r'''
    Config ExtraGrammar = "not /* a comment */";
    /* outer /* nested */ comment */
    @Extract main = align (unlabel (label {3,true})).1;
    ''')
    assert execute(source) == 3


@pytest.mark.parametrize('source', [
    'import "secret"; main = 0;',
    'main = unknown 1;',
    'main = + true 2;',
    'main = if 1 then 2 else 3;',
    'main = fix (\\x:Int. x);',
    'main = {1,2}.0;',
    'main = $ 1;',
    'main = 1; trailing',
])
def test_unsupported_or_bad_semantics_do_not_become_verified_outputs(source):
    with pytest.raises(SourceError):
        execute(parse(source))


def test_declared_range_does_not_silently_wrap_overflow():
    assert execute(parse('main = + 2147483647 1;')) == 2147483648
    with pytest.raises(SourceError, match='range'):
        execute(parse('main = + 2147483647 1;'), signed_bits=32)


def test_nonterminating_false_perspective_exhausts_a_budget():
    source = parse(r'main = (fix (\f:Int -> Int. \x:Int. f x)) 0;')
    with pytest.raises(WorkLimit):
        execute(source, budget=40)


def test_false_transformation_has_a_concrete_original_goal_counterexample():
    original = parse(SUM)
    wrong = parse(SUM.replace('+ h (f t)', 'h'))
    values = linked([2,-3,4])
    assert execute(original, [values]) == 3
    assert execute(wrong, [values]) == 2
