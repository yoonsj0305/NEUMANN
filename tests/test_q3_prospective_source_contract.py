"""Prevent cherry-picked prospective originals or TARGET leakage for Q3.

Synthetic files are only a freeze-contract test, not solved original tasks.
"""
import json
from pathlib import Path
import pytest

from research.q3.q3_coordinate_original_source_gate import (
    freeze_prospective,sha,UPSTREAM)


def test_prospective_originals_hash_selected_before_source_inference(tmp_path):
    directory=tmp_path/"authors"
    directory.mkdir()
    for i in range(1000):
        data={
            "train":[
                {"input":[[i]],"output":[[i+1]]},
                {"input":[[i+2]],"output":[[i+3]]},
                {"input":[[i+4]],"output":[[i+5]]},
            ],
            "test":[{"input":[[i+6]],
                     "output":[["SECRET_HIDDEN_AUTHOR_GOLD"]]}],
        }
        (directory/("task_%04d"%i+".json")).write_text(
            json.dumps(data))
    old={
        "schema":"NEUMANN.Q3.ORIGINAL-ARC2-SOURCE-TEACHING.v1",
        "upstream_revision":UPSTREAM,
        "no_target_gold_in_payload":True,
        "original_source_count":50,
        "original_ids":["task_%04d"%i for i in range(50)],
    }
    manifest=tmp_path/"old.json"
    manifest.write_text(json.dumps(old))
    first=tmp_path/"first.json"
    again=tmp_path/"again.json"
    freeze_prospective(str(directory),str(manifest),str(first))
    freeze_prospective(str(directory),str(manifest),str(again))
    assert sha(first)==sha(again)
    data=json.loads(first.read_text())
    assert data["original_source_count"]==100
    assert data["source_scope"]=="PROSPECTIVE_100_RELATIVE_TO_PRIOR_50_ONLY"
    assert data["no_target_gold_in_payload"] is True
    ids={r["source_id"] for r in data["records"]}
    assert len(ids)==100
    assert not(ids & set(old["original_ids"]))
    assert "SECRET_HIDDEN_AUTHOR_GOLD" not in first.read_text()
    assert '"test"' not in first.read_text()
    assert all(len(r["source_pairs"])==3 for r in data["records"])


def test_bad_prior_registry_fails_closed(tmp_path):
    root=tmp_path/"source"
    root.mkdir()
    prior=tmp_path/"prior.json"
    prior.write_text(json.dumps({"schema":"bad","original_ids":[]}))
    with pytest.raises(ValueError,match="fifty SOURCE"):
        freeze_prospective(str(root),str(prior),str(tmp_path/"out.json"))
