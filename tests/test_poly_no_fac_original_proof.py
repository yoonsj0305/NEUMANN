"""Source-specific proof recipe regression; examples never authorize its PASS."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from neumann1.representation_program import Builder, compile_program, verify_original

PATH = Path(__file__).resolve().parents[1] / "research/development/poly-no-fac-original-proof-2026-10-10/verify.py"
SPEC = importlib.util.spec_from_file_location("poly_no_fac_original_proof", PATH)
PROOF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROOF)


def test_all_universal_identities_are_required():
    result = PROOF.check_identities(PROOF.identities())
    assert result["status"] == "ORIGINAL_CERTIFIED"
    assert {r["obligation"] for r in result["obligations"]} == PROOF.REQUIRED_LAWS
    assert all(r["verification"]["accepted"] for r in result["obligations"])


def test_omitted_or_duplicated_law_cannot_authorize_certificate():
    laws = PROOF.identities()
    assert PROOF.check_identities(laws[:-1])["status"] == "UNKNOWN"
    assert PROOF.check_identities([laws[0]] * 7)["status"] == "UNKNOWN"


def test_changed_composition_cannot_be_certified():
    laws = deepcopy(PROOF.identities())
    bad = next(law for law in laws if law["obligation"] == "CONCAT_SUFFIX_RESPONSE")
    candidate = bad["candidate"]
    b = Builder(candidate["inputs"])
    bad["candidate"] = b.finish([b.const(0)])
    result = PROOF.check_identities(laws)
    assert result["status"] == "UNKNOWN"
    assert result["cause"] == "SUFFICIENT_IDENTITY_NOT_ESTABLISHED"
    assert result["failed_obligation"] == "CONCAT_SUFFIX_RESPONSE"


def test_term_or_work_budget_exhaustion_is_unknown():
    for budget in [{"max_terms": 0}, {"max_product_work": 0}]:
        result = PROOF.check_identities(PROOF.identities(), **budget)
        assert result["status"] == "UNKNOWN"
        assert result["cause"] == "VERIFIER_RESOURCE_OR_SCHEMA_LIMIT"


@pytest.mark.parametrize("field,value", [
    ("original_sha256", "different-source"),
    ("printed_native_solution_sha256", "different-program"),
    ("original_goal", "length of the source list"),
    ("decoded_native_goal", "second component"),
])
def test_source_goal_or_decoder_change_rejected_before_evidence_access(field, value, tmp_path):
    contract = PROOF.read(PATH.with_name("verification_contract.json"))
    contract[field] = value
    with pytest.raises(ValueError, match="binds only"):
        PROOF.analyze(tmp_path, contract)


def test_wrong_composition_has_concrete_witness_but_correctness_is_universal():
    law = next(l for l in PROOF.identities() if l["obligation"] == "CONCAT_SUFFIX_RESPONSE")
    b = Builder(law["candidate"]["inputs"])
    # Wrongly discarding the left factor loses position-dependent coefficients.
    wrong = b.finish([b.add(b.input("lv"), b.input("rv"))])
    result = verify_original(law["original"], wrong)
    assert result["accepted"] is False and result["error"] is None
    row = (2, 1, 1, 2, 1, 2, 0, 1, 0)
    assert compile_program(law["original"]).run([row]) == [(3,)]
    assert compile_program(wrong).run([row]) == [(2,)]
    # This finite disagreement is a counterexample to the deliberately wrong
    # response, not a positive certificate or a flaw in the stored Native.
