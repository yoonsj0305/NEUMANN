"""One preregistered Q3/Q6 original-author, two-semantic causal study.

Uses pinned independent-author official corpora:
- Yale-LILY FOLIO: NL formal logical inference, train and official validation
- BIG-Bench Hard Causal Judgment: verbal causal attribution originals

freeze: choose task IDs *only by salted ID hashes* before observing outcomes,
        serialize model-visible data, SOURCE-only verification labels and
        untouched ORIGINAL TARGET gold to separate artifacts.
infer:  A=frozen model, B=frozen model+past verified source memory,
        C=B+actual neural latent-world update from trusted SOURCE refutations.
        NO original TARGET gold file read or downloaded in infer.
score: original independent TARGET labels accessed only AFTER frozen
       predictions; report C-exclusive over B and matched classical baseline.

Synthetic/fixture successes cannot close global Q3/Q6. A/B/C share model
revision, query inputs, source access, generation and verification budgets.
There is no domain-specific answer generator, heuristic solution operator,
program cache or TARGET feedback in learned policy. SOURCE and TARGET are
different tasks/IDs and labels with cross-task story ID disjointness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import time
from pathlib import Path

MODEL="Qwen/Qwen2.5-Coder-0.5B-Instruct"
REV="ea3f2471cf1b1f0db85067f1ef93848e38e88c25"
FOLIO_COMMIT="5d7bb84c7edab3fb358e057d2807f19cf5cf5e2d"
BBH_COMMIT="9ee07bd481feebf959a6b59d61ea57bdcf30964d"
SALT="NEUMANN.Q3Q6.2026-11-10.V1.FROZEN"
DOMAIN_IDS=("folio_logical_entailment","bbh_causal_attribution")
TRAIN_EPISODES_PER_DOMAIN=2
TARGETS_PER_DOMAIN=4


def canonical(x):
    return json.dumps(x,sort_keys=True,ensure_ascii=True,
                      allow_nan=False,separators=(",",":"))


def digest(s):
    return hashlib.sha256(
        s if isinstance(s,bytes) else s.encode()).hexdigest()


def stable_key(domain,item,*,salt=SALT):
    return digest(salt+"/"+domain+"/"+str(item))


def _rows_folio(path,*,split):
    if split not in ("train","validation"):
        raise ValueError("official FOLIO split required")
    # The original authors use Unknown for TRAIN and Uncertain for VALIDATION.
    # Preserve their exact published labels without outcome-conditioned tuning.
    labels=("True","False","Unknown") if split=="train" else (
        "True","False","Uncertain")
    rows=[]
    for row_number,line in enumerate(Path(path).read_text().splitlines()):
        if not line.strip():
            continue
        r=json.loads(line)
        # Original TRAIN carries story_id/example_id; official VALIDATION
        # carries neither. Never infer identity from the heldout label.
        if not all(k in r for k in ("premises","conclusion","label")):
            raise ValueError("unexpected original FOLIO schema")
        if (not isinstance(r["premises"],list) or
                not isinstance(r["conclusion"],str)):
            raise ValueError("invalid original FOLIO natural language")
        if r["label"] not in labels:
            raise ValueError("unexpected FOLIO original label")
        original_id=r.get("example_id","validation-row-"+str(row_number))
        # Group by actual premise text, not absent official validation ID:
        # multiple target conclusions from the SAME world are not new domains.
        group_id=digest(canonical(r["premises"]))
        rows.append({
            "id":str(original_id),"group_id":group_id,
            "input":{"premises":r["premises"],
                     "conclusion":r["conclusion"],
                     "answer_set":list(labels)},
            "label":r["label"],
        })
    return rows


def _rows_bbh(path):
    corpus=json.loads(Path(path).read_text())
    if not isinstance(corpus.get("examples"),list):
        raise ValueError("unexpected original Causal Judgment schema")
    rows=[]
    for i,r in enumerate(corpus["examples"]):
        if not isinstance(r.get("input"),str) or (
                r.get("target") not in ("Yes","No")):
            raise ValueError("unexpected BBH causal source")
        # 0 and 1 were viewed by researcher while inspecting the schema.
        # Explicitly EXCLUDE them from ALL prospective original tasks.
        if i<2:
            continue
        rows.append({
            "id":str(i),"group_id":str(i),
            "input":{"scenario":r["input"],"answer_set":["Yes","No"]},
            "label":r["target"],
        })
    return rows


def _select_unique_group(rows,domain,*,salt=SALT):
    ordered=sorted(
        rows,key=lambda x:(stable_key(domain,x["id"],salt=salt),x["id"]))
    seen=set()
    result=[]
    for row in ordered:
        if row["group_id"] in seen:
            continue
        seen.add(row["group_id"])
        result.append(row)
    return result


def freeze(*,folio_train,folio_validation,bbh,out_visible,
           out_source_oracle,out_target_gold,out_manifest,
           study_salt=SALT,exclude_register=None):
    """Freeze ID-only cohort; V2 excludes ALL prior visible original groups."""
    if not isinstance(study_salt,str) or len(study_salt)<12:
        raise ValueError("pre-registered label-blind ID salt required")
    previous=None
    if exclude_register is not None:
        previous=json.loads(Path(exclude_register).read_text())
        if not isinstance(previous.get("selected_original_ids"),dict):
            raise ValueError("invalid immutable prior original ID registry")
    sets={
        "folio_logical_entailment":(
            _rows_folio(folio_train,split="train"),
            _rows_folio(folio_validation,split="validation")),
        "bbh_causal_attribution":(
            _rows_bbh(bbh),None),
    }
    visible={"schema":"NEUMANN.Q3Q6.TWO-AUTHOR-ORIGINAL-VISIBLE.v1",
             "training_episodes":[],"evaluation_tasks":[],
             "memory_examples":[]}
    source_hidden=[]
    target_gold=[]
    selections={}
    for domain,(train_rows,test_rows) in sets.items():
        blocked_ids=set()
        blocked_groups=set()
        if previous is not None:
            old=previous["selected_original_ids"][domain]
            for category in (
                "train_original_ids","eval_SOURCE_ids",
                "heldout_original_TARGET_ids"):
                blocked_ids.update(old[category])
            for category in (
                "train_story_ids","source_story_ids","target_story_ids"):
                blocked_groups.update(old[category])
        # Exclude every previously exposed semantic premise/story group,
        # not merely their different row IDs or changed target answers.
        train_rows=[x for x in train_rows if
                    x["id"] not in blocked_ids and
                    x["group_id"] not in blocked_groups]
        if test_rows is not None:
            test_rows=[x for x in test_rows if
                       x["id"] not in blocked_ids and
                       x["group_id"] not in blocked_groups]
        source=_select_unique_group(
            train_rows,domain+"/source",salt=study_salt)
        required_source=(
            TRAIN_EPISODES_PER_DOMAIN*3+TARGETS_PER_DOMAIN*3)
        if len(source)<required_source:
            raise ValueError("not enough distinct author source groups")
        train=source[:TRAIN_EPISODES_PER_DOMAIN*3]
        eval_source=source[
            TRAIN_EPISODES_PER_DOMAIN*3:required_source]
        source_used_ids={x["id"] for x in train+eval_source}
        source_story_ids={x["group_id"] for x in train+eval_source}
        if test_rows is None:
            # Official BBH corpus provides no separate validation file:
            # use a HASH-FROZEN set of original IDs entirely unseen in
            # the training and SOURCE groups. Public, not private blind.
            targets=[x for x in source[required_source:]
                     if x["id"] not in source_used_ids][
                         :TARGETS_PER_DOMAIN]
        else:
            targets=[
                x for x in _select_unique_group(
                    test_rows,domain+"/target",salt=study_salt)
                if x["group_id"] not in source_story_ids][
                    :TARGETS_PER_DOMAIN]
        if len(targets)!=TARGETS_PER_DOMAIN:
            raise ValueError("not enough untouched original author targets")
        for i in range(TRAIN_EPISODES_PER_DOMAIN):
            subset=train[3*i:3*i+3]
            task_id=domain+".train."+str(i)
            visible["training_episodes"].append({
                "domain":domain,"task_id":task_id,
                "demonstration":{"input":subset[0]["input"],
                                 "label":subset[0]["label"]},
                "probe":{"input":subset[1]["input"],
                         "label":subset[1]["label"]},
                "sealed":{"input":subset[2]["input"],
                          "label":subset[2]["label"]},
            })
            # Use exactly one SOURCE-verified prior instance / episode.
            visible["memory_examples"].append({
                "domain":domain,
                "scope":"TRUSTED_SOURCE_ONLY",
                "task_id":task_id,
                "query_id":"prior_observation",
                "query":subset[0]["input"],
                "observed":subset[0]["label"],
            })
        for i,target in enumerate(targets):
            source_three=eval_source[3*i:3*i+3]
            task_id=domain+".original."+target["id"]
            visible["evaluation_tasks"].append({
                "domain":domain,"task_id":task_id,
                "demonstration":{
                    "input":source_three[0]["input"],
                    "label":source_three[0]["label"]},
                "probe":{"input":source_three[1]["input"]},
                "sealed":{"input":source_three[2]["input"]},
                "target":{"input":target["input"],
                          "original_id":target["id"]},
            })
            source_hidden.append({
                "task_id":task_id,
                "probe_label":source_three[1]["label"],
                "sealed_label":source_three[2]["label"],
            })
            target_gold.append({
                "task_id":task_id,"domain":domain,
                "original_id":target["id"],"label":target["label"],
            })
        selections[domain]={
            "train_original_ids":[x["id"] for x in train],
            "eval_SOURCE_ids":[x["id"] for x in eval_source],
            "heldout_original_TARGET_ids":[x["id"] for x in targets],
            "train_story_ids":[x["group_id"] for x in train],
            "source_story_ids":[x["group_id"] for x in eval_source],
            "target_story_ids":[x["group_id"] for x in targets],
        }
        assert not(set(selections[domain]["train_story_ids"]+
                       selections[domain]["source_story_ids"]) &
                   set(selections[domain]["target_story_ids"]))
    assert len(visible["training_episodes"])==4
    assert len(visible["evaluation_tasks"])==8
    assert len(target_gold)==8 and len(source_hidden)==8
    Path(out_visible).write_text(canonical(visible)+"\n")
    Path(out_source_oracle).write_text(canonical(source_hidden)+"\n")
    Path(out_target_gold).write_text(canonical(target_gold)+"\n")
    sources={
        "folio_train":{
            "commit":FOLIO_COMMIT,"sha256":digest(Path(folio_train).read_bytes())},
        "folio_validation":{
            "commit":FOLIO_COMMIT,
            "sha256":digest(Path(folio_validation).read_bytes())},
        "bbh_causal":{
            "commit":BBH_COMMIT,"sha256":digest(Path(bbh).read_bytes())},
    }
    manifest={
        "schema":"NEUMANN.Q3Q6.TWO-AUTHOR-PREREGISTRY.v1",
        "frozen_salt":study_salt,
        "excluded_prior_author_original_register_sha256":(
            digest(Path(exclude_register).read_bytes())
            if exclude_register is not None else None),
        "repository_head":os.getenv("GITHUB_SHA",""),
        "base_model":MODEL,"base_revision":REV,
        "train_episodes_per_domain":TRAIN_EPISODES_PER_DOMAIN,
        "target_originals_per_domain":TARGETS_PER_DOMAIN,
        "one_trainable_core_no_domain_solver":True,
        "no_TARGET_gold_in_model_visible_bundle":True,
        "model_visible_sha256":digest(Path(out_visible).read_bytes()),
        "SOURCE_oracle_sha256":digest(Path(out_source_oracle).read_bytes()),
        "TARGET_gold_sha256":digest(Path(out_target_gold).read_bytes()),
        "public_original_corpus_sha256":sources,
        "selected_original_ids":selections,
        "all_Q1_to_Q7_globally_unproven":True,
        "prior_PR_title_body_search_FOLIO_and_BBH_zero_matches":True,
        "full_prior_repo_or_pretraining_exposure_audit":"UNKNOWN",
        "benchmark_pretraining_contamination_not_excluded":True,
    }
    Path(out_manifest).write_text(canonical(manifest)+"\n")
    print("Q3Q6_FROZEN_ID_ONLY",{
        "per_domain":TARGETS_PER_DOMAIN,
        "train_episodes_per_domain":TRAIN_EPISODES_PER_DOMAIN,
        "target_labels_not_in_visible_bundle":True,
        "visible_sha256":manifest["model_visible_sha256"],
        "target_sha256":manifest["TARGET_gold_sha256"],
        "source_commits":[FOLIO_COMMIT,BBH_COMMIT]},flush=True)


def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="cmd",required=True)
    f=sub.add_parser("freeze")
    for n in ("folio-train","folio-validation","bbh",
              "out-visible","out-source-oracle",
              "out-target-gold","out-manifest"):
        f.add_argument("--"+n,required=True)
    f.add_argument("--study-salt",default=SALT)
    f.add_argument("--exclude-register")
    a=p.parse_args()
    if a.cmd=="freeze":
        freeze(folio_train=a.folio_train,
               folio_validation=a.folio_validation,bbh=a.bbh,
               out_visible=a.out_visible,
               out_source_oracle=a.out_source_oracle,
               out_target_gold=a.out_target_gold,
               out_manifest=a.out_manifest,
               study_salt=a.study_salt,
               exclude_register=a.exclude_register)


if __name__=="__main__":
    main()
