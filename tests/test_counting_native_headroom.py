from experiments.counting_native_headroom import decision_summary, exact_count


def test_exact_zero_and_large_integer_are_supported():
    assert exact_count("s SATISFIABLE\nc s type mc\nc s exact arb int 0\nc s pac guarantees epsilon: 0 delta: 0\n", "ganak") == 0
    assert exact_count("s 123456789012345678901234567890\n", "d4") == 123456789012345678901234567890


def test_float_summary_cannot_replace_exact_ganak_result():
    assert exact_count("s mc 12.0\n", "ganak") is None


def test_counter_without_successful_proof_is_not_valid():
    assert exact_count("Regular model count = 6\n", "cpog") is None
    assert exact_count("FULL-PROOF SUCCESS\nRegular model count = 6\n", "cpog") == 6


def test_malformed_disagreeing_and_fractional_results_fail_closed():
    for text in ["c s exact arb int bad\n", "c s exact arb int 1\nc s exact arb int 2\n", "c s exact arb int 1/2\n", "c s exact arb int -1\n"]:
        assert exact_count(text, "ganak") is None


def test_partial_success_cannot_pass_screen():
    contract = {"cases": [1, 2]}
    rows = [{"status": "VERIFIED", "native_over_free": 1000, "complexity_bin": "variables_le_200"},
            {"status": "INCOMPLETE", "native_over_free": None, "complexity_bin": "variables_gt_200"}]
    result = decision_summary(contract, rows)
    assert result["status"] == "INCOMPLETE"
    assert not result["headroom_screen_met"] and not result["G1_admitted"]


def test_large_bin_cannot_be_hidden_by_geomean():
    contract = {"cases": [1, 2]}
    rows = [{"status": "VERIFIED", "native_over_free": 10000, "complexity_bin": "variables_le_200"},
            {"status": "VERIFIED", "native_over_free": 1, "complexity_bin": "variables_gt_200"}]
    assert not decision_summary(contract, rows)["headroom_screen_met"]


def test_diagnostic_success_never_admits_learning():
    contract = {"cases": [1, 2]}
    rows = [{"status": "VERIFIED", "native_over_free": 11, "complexity_bin": label}
            for label in ["variables_le_200", "variables_gt_200"]]
    result = decision_summary(contract, rows)
    assert result["headroom_screen_met"]
    assert not result["G1_admitted"] and result["complete_system_cost_advantage"] == "UNKNOWN"
