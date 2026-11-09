"""Original-source transfer smoke test, not an independent first claim.

One fully SOURCE-certified external author program for character frequency
contained the reusable executable subexpression set(x). A DIFFERENT
external original requires the transformation sum(set(x)). This verifies
that source-derived fragment transfer can construct a new task program from
a failing model proposal sum(x), without task IDs, expected target solution,
or human-written per-task replacement templates.
"""
from pathlib import Path

from neumann1.open_program_inventor import Attempt,IsolatedPython
from neumann1.verified_fragment_transfer import (
    CertifiedFragmentLibrary,transfer_from_verified_sources)

LIBRARY=Path(__file__).resolve().parents[1]/(
    "research/q3/verified_prior_codearc_source_library.json")


def test_previous_original_generated_fragment_crosses_string_to_list():
    runner=IsolatedPython(max_seconds=12)
    previous=CertifiedFragmentLibrary.load(LIBRARY).certify(runner)
    assert len(previous.records)==6
    assert "set(x)" in previous.fragments
    # These are from original CodeARC 801 SOURCE examples, already exposed
    # elsewhere in the project; they are a regression, not fresh Q6 proof.
    source=[
        ([1,2,3,4,5],15),
        ([1,1,2,2,3,3],6),
        ([10,20,30,10,40,50],150),
        ([100,200,300,400],1000),
        ([42,42,42,42],42),
        ([5,10,15,20,25,30],105)]
    independent=[([-1,-1,-2,-3,-4],-10)]
    initial=Attempt(
        "model_program_sha",3,6,"EXECUTED",0,
        "def transform(x):\n    return sum(x)")
    outcome=transfer_from_verified_sources(
        (initial,),source,independent,previous,runner,
        max_variants_per_program=32,exclude_origin_ids=("801",))
    assert outcome.status=="SOURCE_VERIFIED_TRANSFERRED_FRAGMENT",outcome
    assert outcome.source_candidates_checked>0
    assert outcome.program is not None
    assert "set(x)" in outcome.program
    check=runner.evaluate(outcome.program,[[1,1,5,2,5]])
    assert check.status=="EXECUTED"
    assert check.outputs==(8,)


def test_mismatched_old_source_signature_fails_closed(tmp_path):
    runner=IsolatedPython(max_seconds=12)
    data={
        "schema":"NEUMANN.Q3.INDEPENDENT.SOURCE.MACROS.v1",
        "records":[{
            "external_original_id":690,
            "program":"def transform(x):\n    return x",
            "program_sha256":"invalid",
            "source_pairs":[["abc","abc"],["xyz","xyz"]]}]}
    import json
    path=tmp_path/"wrong.json"
    path.write_text(json.dumps(data))
    import pytest
    with pytest.raises(ValueError,match="tampered"):
        CertifiedFragmentLibrary.load(path)
