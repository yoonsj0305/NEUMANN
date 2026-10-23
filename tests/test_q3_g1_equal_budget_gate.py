"""Gate correctness test; *NOT* a passing NEUMANN Q3 model evaluation.

The selftest constructs eight SYNTHETIC fictional rows only to exercise
scientific decision logic, then six invalid claims which must be rejected.
"""
def test_q3_budgeted_gate_synthetic_positive_six_negative_contracts():
    from research.q3.g1_equal_budget_admission_guard import selftest
    selftest()
