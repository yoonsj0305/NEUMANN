from research.q3.discovery_policy.native_original_solver_outcome_taxonomy_20261028 import classify_native_process

def test_native_timeout_stderr_must_not_be_called_parser_failure():
    assert classify_native_process("", "cvc5 interrupted by timeout.\n", 0)=="BUDGET_HOLD_UNPROVED"

def test_native_budget_signal_fails_closed():
    assert classify_native_process("", "", -24)=="BUDGET_HOLD_UNPROVED"
    assert classify_native_process("", "", 0,forced=True)=="BUDGET_HOLD_UNPROVED"

def test_native_legacy_sygus_parser_error_is_not_time_limit():
    assert classify_native_process(
        '(error "Parse Error: Symbol int.to.str not declared")', "", 1
    )=="NATIVE_PARSER_OR_UNSUPPORTED_HOLD"

def test_native_program_is_not_a_semantic_proof():
    assert classify_native_process(
        '((define-fun f ((x Int)) Int x))', "", 0
    )=="NATIVE_CANDIDATE_REQUIRES_INDEPENDENT_ORIGINAL_PROOF"

def test_synthesizer_infeasible_without_certificate_remains_hold():
    assert classify_native_process("infeasible\n","",0)=="NATIVE_INFEASIBLE_CLAIM_REQUIRES_PROOF"

def test_no_output_is_not_classified_as_unsolvable():
    assert classify_native_process("","",0)=="NATIVE_NO_PROGRAM_UNDETERMINED_HOLD"

def test_nonzero_exit_is_not_timeout_automatically():
    assert classify_native_process("","generic exception",1)=="NATIVE_PARSER_OR_UNSUPPORTED_HOLD"
