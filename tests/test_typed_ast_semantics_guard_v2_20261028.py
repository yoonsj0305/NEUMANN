from research.q3.discovery_policy.typed_ast_semantics_guard_v2_20261028 import (
    TypedPolynomialAST,canonicalize_observations,decode_multiply_eos,
    compile_executable_ast,exact_trace_match_does_not_imply_proof,
    classify_architecture_result)

def test_translation_covariant_observations_exactly_invariant():
    a=canonicalize_observations([(0,3),(1,8),(2,13)])
    b=canonicalize_observations([(7,3),(8,8),(9,13)])
    assert a==b==((0,3),(1,8),(2,13))

def test_global_polynomial_shift_not_co_moving():
    a=canonicalize_observations([(0,0),(1,1),(2,4)])
    b=canonicalize_observations([(2,4),(3,9),(4,16)])
    assert a!=b

def test_valid_variable_length_ast_with_real_eos():
    assert decode_multiply_eos([1,1,1,1,0,1])==4

def test_reject_missing_eos():
    assert decode_multiply_eos([1]*7) is None
    assert decode_multiply_eos([1]*6) is None

def test_reject_zero_length_invalid_token():
    assert decode_multiply_eos([0]) is None
    assert decode_multiply_eos([1,3,0]) is None

def test_executable_ast_uses_typed_relative_coordinate():
    s=compile_executable_ast(TypedPolynomialAST(4,3,-2,7))
    assert s.startswith('(define-fun inv ((x Int) (y Int)) Bool')
    assert s.count('(- x 7)')==4

def test_trace_fit_not_formal_correctness():
    assert not exact_trace_match_does_not_imply_proof(True,['unsat','sat','unsat'])
    assert exact_trace_match_does_not_imply_proof(True,['unsat','unsat','unsat'])

def test_toy_no_G1_pass():
    assert classify_architecture_result(False,False,False,True)=='G1_HOLD'

def test_never_auto_promote_sufficient_flags():
    assert classify_architecture_result(True,True,True,True)=='NEEDS_INDEPENDENT_SCIENTIFIC_REVIEW'
