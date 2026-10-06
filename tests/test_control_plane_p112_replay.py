"""P1.12 model-free joint-logit replay is independent of model execution."""
import copy
import pytest

from experiments.control_plane_p112_catalog import catalog
from experiments.control_plane_p112_replay import replay_record
from experiments.control_plane_p112_runtime import run_item
from tests.test_control_plane_p112_runtime import FixtureCrossEncoder


def test_exact_original_verifier_replay_with_no_model():
    rows,refs=catalog()
    record=run_item(rows[0],refs[0],FixtureCrossEncoder(winner=refs[0]["expected_candidate"]))
    assert record["status"]=="ACCEPTED"
    replay_record(rows[0],refs[0],record)


def test_tampering_selected_candidate_is_detected():
    rows,refs=catalog()
    rec=run_item(rows[1],refs[1],FixtureCrossEncoder(winner=refs[1]["expected_candidate"]))
    altered=copy.deepcopy(rec)
    altered["selected_candidate"]=1
    with pytest.raises(ValueError,match="semantic replay drift"):
        replay_record(rows[1],refs[1],altered)


def test_tampering_joint_ir_digest_is_detected():
    rows,refs=catalog()
    rec=run_item(rows[0],refs[0],FixtureCrossEncoder(winner=refs[0]["expected_candidate"]))
    altered=copy.deepcopy(rec)
    altered["selector_receipt"]["joint_ir_sha256"]="0"*64
    with pytest.raises(ValueError,match="joint|semantic"):
        replay_record(rows[0],refs[0],altered)
