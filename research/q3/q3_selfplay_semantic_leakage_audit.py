"""Validity audit of frozen selfplay world holdout, NOT new Q3 training.

Decision changed: when a synthetic heldout program is observationally
equivalent to a training program on fixed cross-world probes, suppress its
independent transfer claim. If none collide, retain only a *finite-probe
distinct* label; this still cannot prove unrelated semantic-domain transfer,
and no synthetic program changes into an original independently authored task.

No extra model calls, no expansion of the 48-world generation run.
"""
from __future__ import annotations

import argparse,hashlib,json
from pathlib import Path

from neumann1.open_program_inventor import IsolatedPython
from research.q3.q3_selfplay_worlds import SCHEMA,KINDS,canonical,make_json_inputs

PROBE_SEEDS=(317,911,2027)


def _read(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines()
            if x.strip()]


def audit(train,heldout,out):
    a=_read(train);b=_read(heldout)
    if not a or not b:
        raise ValueError("frozen train and heldout world records required")
    ids=[w["program_sha256"] for w in (*a,*b)]
    if len(set(ids))!=len(ids):
        raise ValueError("training/heldout program SHA collision")
    runner=IsolatedPython(max_seconds=8)
    fingerprints={}
    executions={}
    for kind in KINDS:
        inputs=[v for seed in PROBE_SEEDS
                for v in make_json_inputs(kind,seed,n=6)]
        for w in (*a,*b):
            if w.get("schema")!=SCHEMA:
                raise ValueError("not original model-authored code-world schema")
            if w["program_generation_type"]!=kind:
                continue
            resp=runner.evaluate(w["program"],inputs)
            if resp.status!="EXECUTED" or len(resp.outputs)!=len(inputs):
                executions[w["program_sha256"]]=resp.status
                continue
            key=canonical(resp.outputs)
            fingerprints[w["program_sha256"]]=hashlib.sha256(
                key.encode()).hexdigest()
            executions[w["program_sha256"]]="EXECUTED"
    # SHA-distinct training programs can still encode the same behavior.
    # Counting them as independent invented methods inflates the diversity
    # of the self-generated curriculum, even if the heldout is separate.
    training_behavioral_collisions=[]
    for i,t in enumerate(a):
        for other in a[i+1:]:
            if (t["program_generation_type"]==other["program_generation_type"]
                and t["program_sha256"] in fingerprints
                and other["program_sha256"] in fingerprints
                and fingerprints[t["program_sha256"]]==fingerprints[
                    other["program_sha256"]]):
                training_behavioral_collisions.append({
                    "train_sha_1":t["program_sha256"],
                    "train_sha_2":other["program_sha256"],
                    "kind":t["program_generation_type"],
                })
    effective_train_behavior_classes=len({
        (t["program_generation_type"],
         fingerprints[t["program_sha256"]])
        for t in a if t["program_sha256"] in fingerprints})
    collisions=[]
    for h in b:
        for t in a:
            if (h["program_generation_type"]==t["program_generation_type"]
                and h["program_sha256"] in fingerprints
                and t["program_sha256"] in fingerprints
                and fingerprints[h["program_sha256"]]==fingerprints[t["program_sha256"]]):
                collisions.append({
                    "heldout_sha":h["program_sha256"],
                    "train_sha":t["program_sha256"],
                    "kind":h["program_generation_type"],
                })
    result={
        "schema":"NEUMANN.Q3.SELFPLAY-SYNTHETIC-LEAKAGE-AUDIT.v1",
        "train":len(a),"heldout":len(b),
        "probes_per_kind":len(PROBE_SEEDS)*6,
        "kind_is_not_semantic_family":True,
        "program_SHA_disjoint":True,
        "finite_probe_exact_behavioral_collisions":collisions,
        "train_behavioral_collisions":training_behavioral_collisions,
        "train_distinct_observed_behavior_classes":effective_train_behavior_classes,
        "unexecutable_probe_worlds":[
            {"sha":k,"status":v} for k,v in executions.items()
            if v!="EXECUTED"],
        "heldout_distinct_on_finite_probes_only":len(collisions)==0 and
            all(w["program_sha256"] in fingerprints for w in b),
        "independent_author_new_semantic_families_proven":False,
        "unseen_original_target_gold_read":False,
        "q3_global":"OPEN","q6_global":"OPEN",
    }
    Path(out).write_text(canonical(result)+"\n")
    print("Q3Q6_FROZEN_SELFPLAY_SEMANTIC_LEAKAGE_VERDICT",
          result,flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--train",required=True)
    p.add_argument("--heldout",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    audit(args.train,args.heldout,args.out)
