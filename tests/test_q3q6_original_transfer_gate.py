"""Data provenance, honest scoring, SOURCE/TARGET separation regressions.

Fixtures are synthetic and excluded from scientific Q3/Q6 original scores.
"""
from __future__ import annotations

import json
from pathlib import Path

from research.q3.q3q6_two_author_freeze import freeze
from research.q3.q3q6_original_transfer_run import score
from research.q3.q3q6_two_author_freeze import canonical,digest


def test_original_corpus_freeze_separates_target_gold_from_model(tmp_path):
    folio_train=tmp_path/"folio_train.jsonl"
    folio_validation=tmp_path/"folio_valid.jsonl"
    bbh=tmp_path/"causal.json"
    ftrain=[
        {"story_id":i,"example_id":i,
         "premises":["P if Q; Q","Text "+str(i)],
         "conclusion":"P? "+str(i),
         "label":("True","False","Uncertain")[i%3]}
        for i in range(34)]
    fvalid=[
        {"story_id":100+i,"example_id":100+i,
         "premises":["Separate "+str(i)],
         "conclusion":"Check "+str(i),
         "label":("True","False","Uncertain")[i%3]}
        for i in range(12)]
    folio_train.write_text("".join(canonical(x)+"\n" for x in ftrain))
    folio_validation.write_text("".join(canonical(x)+"\n" for x in fvalid))
    bbh.write_text(canonical({"examples":[
        {"input":"Is X the cause in original "+str(i)+"?",
         "target":("Yes" if i%2 else "No")}
        for i in range(35)]}))
    visible=tmp_path/"visible.json"
    source=tmp_path/"source.json"
    gold=tmp_path/"gold.json"
    manifest=tmp_path/"manifest.json"
    freeze(
        folio_train=folio_train,folio_validation=folio_validation,
        bbh=bbh,out_visible=visible,out_source_oracle=source,
        out_target_gold=gold,out_manifest=manifest)
    v=json.loads(visible.read_text())
    m=json.loads(manifest.read_text())
    g=json.loads(gold.read_text())
    assert len(v["training_episodes"])==4
    assert len(v["evaluation_tasks"])==8
    assert len(g)==8
    assert "target_label" not in visible.read_text()
    assert all("label" not in t["target"] for t in
               v["evaluation_tasks"])
    assert all(set(m["selected_original_ids"][domain][
        "heldout_original_TARGET_ids"]).isdisjoint(
        m["selected_original_ids"][domain]["train_original_ids"]+
        m["selected_original_ids"][domain]["eval_SOURCE_ids"])
        for domain in ("folio_logical_entailment",
                       "bbh_causal_attribution"))
    assert digest(visible.read_bytes())==m["model_visible_sha256"]
    assert digest(gold.read_bytes())==m["TARGET_gold_sha256"]
    # Freeze output is stable across separate reads (ignoring environment
    # commit SHA), and selection does not consult label contents.
    altered=json.loads(bbh.read_text())
    for row in altered["examples"]:
        row["target"]="Yes" if row["target"]=="No" else "No"
    bbh.write_text(canonical(altered))
    freeze(
        folio_train=folio_train,folio_validation=folio_validation,
        bbh=bbh,out_visible=visible,out_source_oracle=source,
        out_target_gold=gold,out_manifest=manifest)
    again=json.loads(manifest.read_text())
    assert again["selected_original_ids"]==m["selected_original_ids"]


def test_exact_scorer_refuses_to_promote_non_learning_to_new_intelligence(tmp_path):
    manifest={
        "model_visible_sha256":"visible-source-sha",
        "SOURCE_oracle_sha256":"source-check-sha",
    }
    domains=["folio_logical_entailment"]*4+["bbh_causal_attribution"]*4
    gold=[
        {"task_id":f"test-{i}","domain":domains[i],
         "original_id":str(i),
         "label":"True" if i<4 else "Yes"}
        for i in range(8)]
    gold_path=tmp_path/"gold.json"
    gold_path.write_text(canonical(gold)+"\n")
    manifest["TARGET_gold_sha256"]=digest(gold_path.read_bytes())
    m_path=tmp_path/"manifest.json"
    m_path.write_text(canonical(manifest)+"\n")
    by_arm={}
    for arm in ("A","B","C"):
        by_arm[arm]=[
            {"task_id":f"test-{i}","domain":domains[i],
             "source_certified":arm=="C",
             "status":"CERTIFIED_SOURCE" if arm=="C" else "ABSTAIN",
             "elapsed_seconds":0.25,
             "frozen_submitted_prediction":(
                 "True" if i<4 else "Yes") if arm=="C" else None,
             "frozen_raw_diagnostic_prediction":(
                 "True" if i<4 else "Yes") if arm=="C" else None,
             "classical_matched_source_prediction":None}
            for i in range(8)]
    pred={
        "schema":"NEUMANN.Q3Q6.ORIGINAL-UNSEEN-PREDICTIONS.v1",
        "visible_sha256":manifest["model_visible_sha256"],
        "source_oracle_sha256":manifest["SOURCE_oracle_sha256"],
        "original_TARGET_gold_read":False,
        "C_actual_weight_updates":0,
        "C_weight_delta_l1":0.0,
        "A_B_C":by_arm,
    }
    p=tmp_path/"pred.json"
    p.write_text(canonical(pred)+"\n")
    out=tmp_path/"scored.json"
    score(p,gold_path,m_path,out)
    s=json.loads(out.read_text())
    assert not s["causal_two_domain_initial_condition"]
    assert all(v["C_exact"]==4 for v in s["domains"].values())
    assert s["Q3_global"]==s["Q6_global"]=="OPEN"
