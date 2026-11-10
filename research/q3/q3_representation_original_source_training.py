"""Q3 graph representation policy trained on ORIGINAL ARC-AGI-2 SOURCE only.

Two irreversible phases:
  freeze: source-author registry, copy only ORIGINAL TRAIN observations, never
          serialize test inputs/answers into learner payload.
  learn: consume frozen SOURCE_ONLY.json only; execute each invented
         representation on an independent SOURCE check in Docker and learn
         positive AND negative evidence. No model target labels or author
         original test outputs are read during inference.

This is a source-only discovery policy experiment, NOT a frontier Q3 PASS.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from neumann1.open_program_inventor import IsolatedPython
from neumann1.q3_representation_policy import LearnedRepresentationPrior

UPSTREAM="f3283f727488ad98fe575ea6a5ac981e4a188e49"
SCHEMA="NEUMANN.Q3.ORIGINAL-ARC2-SOURCE-TEACHING.v1"


def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),
                      ensure_ascii=True,allow_nan=False)


def digest(p):
    return sha256(Path(p).read_bytes()).hexdigest()


def freeze(original_root,out,*,limit=64):
    if not 1<=limit<=256:
        raise ValueError("registered SOURCE teaching limit 1-256")
    root=Path(original_root)
    all_files=sorted(root.glob("*.json"))
    if len(all_files)!=1000:
        raise ValueError("original ARC-AGI-2 author revision expected 1000 tasks")
    # Exactly previous immutable SOURCE registry selection:
    # neumann1.arc2_meta_grid_reasoner.source_paths() is based on
    # SHA2 of (salt, original SOURCE filename), not on task performance.
    from neumann1.arc2_meta_grid_reasoner import source_paths
    old_sources,_=source_paths()
    ids=[path.stem for path in old_sources[:limit]]
    rows=[];skipped=[]
    for original_id in ids:
        file=root/(original_id+".json")
        source_file_digest=digest(file)
        o=json.loads(file.read_text())
        train=o.get("train")
        if not isinstance(train,list) or len(train)<3:
            skipped.append(original_id);continue
        train_only=[[pair["input"],pair["output"]] for pair in train]
        if len(train_only)>32:
            skipped.append(original_id);continue
        keys=[canonical(p[0]) for p in train_only]
        if len(keys)!=len(set(keys)):
            skipped.append(original_id);continue
        rows.append({
            "source_id":original_id,
            "original_author_file_sha256":source_file_digest,
            "source_pairs":train_only,
            "source_train":train_only[:-1],
            "source_independent_checks":train_only[-1:],
        })
    report={
        "schema":SCHEMA,
        "upstream_revision":UPSTREAM,
        "source_registry":"neumann-source-shuffle-v1:first-"+str(limit),
        "original_source_count":len(rows),
        "skipped_source_ids":skipped,
        "original_ids":[x["source_id"] for x in rows],
        "records":rows,
        "no_target_gold_in_payload":True,
        "q3_global":"OPEN",
    }
    Path(out).write_text(canonical(report)+"\n")
    assert '"test"' not in Path(out).read_text()
    print("Q3_FROZEN_REAL_ARC2_SOURCE_ONLY",len(rows),
          len(skipped),digest(out),flush=True)


def learn(source_only,out):
    observed=json.loads(Path(source_only).read_text())
    if (observed.get("schema")!=SCHEMA
            or observed.get("upstream_revision")!=UPSTREAM
            or observed.get("no_target_gold_in_payload") is not True
            or len(observed.get("records",[]))!=
                  observed.get("original_source_count")):
        raise ValueError("original SOURCE registry missing or corrupted")
    rows=observed["records"]
    trials=[(r["source_id"],r["source_train"],
             r["source_independent_checks"]) for r in rows]
    runner=IsolatedPython(max_seconds=8)
    prior=LearnedRepresentationPrior.learn_source_trials(
        trials,runner,max_episodes=256)
    snapshot=prior.source_snapshot()
    snapshot.update({
        "training_original_author":"ARC-AGI-2",
        "training_original_revision":UPSTREAM,
        "frozen_source_only_sha256":digest(source_only),
        "source_teacher_count":len(trials),
        "algorithm":"one_source_only_graph_representation_policy_v1",
    })
    Path(out).write_text(canonical(snapshot)+"\n")
    print("Q3_REAL_SOURCE_REPRESENTATION_POLICY_LEARNED",
          {**prior.evidence(),
           "source_originals":len(trials),
           "source_snapshot_sha256":digest(out)},flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    p=parser.add_subparsers(dest="cmd",required=True)
    x=p.add_parser("freeze")
    x.add_argument("--original-root",required=True)
    x.add_argument("--out",required=True)
    x.add_argument("--limit",type=int,default=64)
    y=p.add_parser("learn")
    y.add_argument("--source-only",required=True)
    y.add_argument("--out",required=True)
    a=parser.parse_args()
    if a.cmd=="freeze":
        freeze(a.original_root,a.out,limit=a.limit)
    else:
        learn(a.source_only,a.out)
