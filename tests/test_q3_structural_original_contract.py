"""Two-origin Q3 author-original freeze and independent scoring contracts.

All data in this test are synthetic *contract fixtures*, NEVER Q3 successes.
"""
import json
import hashlib
import pytest

from research.q3.q3_structural_original_gate import (
    freeze_arcana,sha_file,score,SCHEMA)


def test_source_only_blind_excludes_external_original_gold(tmp_path):
    originals=tmp_path/"author"
    originals.mkdir()
    for i in range(8):
        fixture={
            "train":[
                {"input":[[i]],"output":[[i+1]]},
                {"input":[[i+2]],"output":[[i+3]]},
                {"input":[[i+4]],"output":[[i+5]]},
            ],
            "test":[{"input":[[i+6]],"output":[["SECRET_HIDDEN_ORIGINAL"]]}],
        }
        (originals/f"author_{i}.json").write_text(json.dumps(fixture))
    blind=tmp_path/"blind.json"
    freeze_arcana(str(originals),str(blind))
    data=json.loads(blind.read_text())
    assert data["schema"]==SCHEMA
    assert data["origin"]=="arcana"
    assert data["scope"]=="FIRST_AUTHOR_BLIND"
    assert data["no_target_gold_in_blind"]
    assert "SECRET_HIDDEN_ORIGINAL" not in blind.read_text()
    assert len(data["records"])==4
    assert all("test" not in x and "target_inputs" in x
               for x in data["records"])


def test_author_gold_scorer_requires_preexisting_sha_and_never_declares_q3(tmp_path):
    root=tmp_path/"author"
    root.mkdir()
    for i in range(7):
        rec={
            "train":[{"input":[[j+i]],"output":[[j+i+1]]}
                     for j in (0,2,4)],
            "test":[{"input":[[i+6]],"output":[[i+7]]}],
        }
        (root/f"author_{i}.json").write_text(json.dumps(rec))
    blind=tmp_path/"blind.json"
    freeze_arcana(str(root),str(blind))
    data=json.loads(blind.read_text())
    frozen={
        "schema":"NEUMANN.Q3.STRUCTURAL-PREDICTIONS.v1",
        "blind_sha256":sha_file(blind),
        "target_gold_accessed":False,
        "origin":"arcana",
        "records":[],
    }
    for row in data["records"]:
        answer=json.loads((root/row["id"]).read_text())["test"][0]["output"]
        frozen["records"].append({
            "id":row["id"],"source_output_diverse":True,
            "native":[],"arms":{
                a:{"source_verified":a=="C",
                   "original_target_predictions":[answer] if a=="C" else [],
                   "new_not_in_prior_teacher_programs":a=="C"}
                for a in ("A","B","C")}})
    predictions=tmp_path/"predictions.json"
    predictions.write_text(json.dumps(frozen))
    out=tmp_path/"score.json"
    score(str(blind),str(predictions),sha_file(predictions),str(root),str(out))
    result=json.loads(out.read_text())["summary"]
    assert result["C_new_executable_original_exact"]==4
    assert result["C_exclusive_nonconstant"]==4
    assert result["q3_global"]=="OPEN"
    with pytest.raises(ValueError,match="SHA"):
        score(str(blind),str(predictions),"0"*64,str(root),str(out))


def test_no_nonconstant_credit_from_constant_source_output(tmp_path):
    # This is a scientific contract, not a solved novel original problem.
    root=tmp_path/"originals"
    root.mkdir()
    for i in range(4):
        rec={
            "train":[{"input":[[j]],"output":[[1]]}
                     for j in (1,2,3)],
            "test":[{"input":[[4]],"output":[[1]]}],
        }
        (root/f"t{i}.json").write_text(json.dumps(rec))
    blind=tmp_path/"blind.json"
    freeze_arcana(str(root),str(blind))
    data=json.loads(blind.read_text())
    predicted={
        "schema":"NEUMANN.Q3.STRUCTURAL-PREDICTIONS.v1",
        "origin":"arcana",
        "blind_sha256":sha_file(blind),
        "target_gold_accessed":False,
        "records":[{
            "id":r["id"],"source_output_diverse":False,
            "native":[],"arms":{
                k:{"source_verified":k=="C",
                   "original_target_predictions":[[[1]]] if k=="C" else [],
                   "new_not_in_prior_teacher_programs":k=="C"}
                for k in ("A","B","C")}
        } for r in data["records"]]
    }
    output=tmp_path/"predictions.json"
    output.write_text(json.dumps(predicted))
    final=tmp_path/"results.json"
    score(str(blind),str(output),sha_file(output),str(root),str(final))
    summary=json.loads(final.read_text())["summary"]
    assert summary["C"]==4
    assert summary["C_exclusive_nonconstant"]==0
    assert summary["C_new_executable_original_exact"]==0



def test_next_eight_external_originals_pre_registered_and_old_ones_excluded(tmp_path):
    from research.q3.q3_structural_original_gate import freeze_arcana_next8
    root=tmp_path/"external"
    root.mkdir()
    specimen={
        "train":[{"input":[[i]],"output":[[i+1]]}
                 for i in (0,2,4)],
        "test":[{"input":[[6]],"output":[["HIDDEN_ORIGINAL_GOLD"]]}],
    }
    for i in range(16):
        (root/f"independent_{i}.json").write_text(json.dumps(specimen))
    for old in ("archimedes1.json","magnetic1.json","mop2.json",
                "cup1.json","pocket_watch1.json"):
        (root/old).write_text(json.dumps(specimen))
    out=tmp_path/"NEW_BLIND.json"
    freeze_arcana_next8(str(root),str(out))
    frozen=json.loads(out.read_text())
    assert frozen["scope"]=="NEWLY_FROZEN_AUTHOR_ORIGINALS_NO_TUNING"
    assert frozen["origin"]=="arcana"
    assert len(frozen["records"])==8
    assert len({r["id"] for r in frozen["records"]})==8
    assert not ({r["id"] for r in frozen["records"]} &
                set(frozen["prior_excluded"]))
    assert frozen["no_target_gold_in_blind"] is True
    assert "HIDDEN_ORIGINAL_GOLD" not in out.read_text()
    assert all("target_inputs" in r and "test" not in r
               for r in frozen["records"])



def test_second_author_source_cohort_disjoint_and_original_gold_unseen(tmp_path):
    from research.q3.q3_structural_original_gate import freeze_arcana_next8
    d=tmp_path/"author"
    d.mkdir()
    payload={
        "train":[{"input":[[i]],"output":[[i+1]]}
                 for i in (0,2,4)],
        "test":[{"input":[[13]],"output":[["ORIGINAL_GOLD_NOT_ALLOWED"]]}],
    }
    for i in range(25):
        (d/f"new_author_{i}.json").write_text(json.dumps(payload))
    first=tmp_path/"first.json"
    second=tmp_path/"second.json"
    freeze_arcana_next8(str(d),str(first))
    freeze_arcana_next8(str(d),str(second),skip=8)
    p=json.loads(first.read_text())
    q=json.loads(second.read_text())
    assert p["scope"]=="NEWLY_FROZEN_AUTHOR_ORIGINALS_NO_TUNING"
    assert q["scope"]=="SECOND_DISJOINT_SOURCE_AUTHOR_ORIGINALS"
    assert len(q["records"])==8
    assert not ({r["id"] for r in p["records"]} &
                {r["id"] for r in q["records"]})
    assert set(q["prior_first_eight_ids"])=={r["id"] for r in p["records"]}
    assert set(q["prior_first_eight_ids"]).issubset(set(q["prior_excluded"]))
    assert "ORIGINAL_GOLD_NOT_ALLOWED" not in second.read_text()
    assert q["no_target_gold_in_blind"] is True
