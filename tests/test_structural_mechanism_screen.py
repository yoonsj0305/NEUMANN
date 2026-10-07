import pytest
from experiments.structural_mechanism_screen import proof_case
from neumann1.public_rewrite_search import propose
from neumann1.representation_program import verify_original
from neumann1.representation_rewrite_certificate import check_certificate


@pytest.mark.parametrize("motif", ["ONE_STEP", "COMPOSED", "FALSE_SHARED"])
def test_unscored_program_fixture_preserves_goal_and_wrong_premise_is_rejected(motif):
    case = proof_case({"motif": motif, "degree": 1, "seed": 42}, {"rows": 4})
    result = propose(case["original"])
    assert verify_original(case["original"], result["candidate"])["accepted"]
    if result["certificate"]["steps"]:
        assert check_certificate(case["original"], result["candidate"], result["certificate"])["accepted"]
    if motif == "FALSE_SHARED":
        assert not check_certificate(case["original"], result["candidate"], case["false_certificate"])["accepted"]
