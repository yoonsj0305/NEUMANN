"""Final single bounded Q3/Q6 original-author same-mechanism study.

Precommitted decision: retain latent-source learning for independent replication ONLY if
C learns from signed SOURCE, revises its own hypothesis, and has >=1 sealed-SOURCE-
certified exact original TARGET exclusive of B and a classical source-only control
in BOTH SCAN compositional commands and ARC visual transformations.
Otherwise STOP this mechanism. This is not global Q3/Q6 proof.
Gold is generated in a separate preparation job, never present in inference.
"""
from __future__ import annotations
import argparse
import gc
import hashlib
import json
import re
import time
from pathlib import Path

from neumann1.causal_experience import CausalExperienceCore
from neumann1.q3_latent_world_policy import TrainableLatentWorldPolicy

SALT = "NEUMANN.Q3Q6.FINAL.ONE.SAME.WORLD.2026-11-11.FROZEN"
REV = "ea3f2471cf1b1f0db85067f1ef93848e38e88c25"
SCAN_COMMIT = "c4b756cbc010d75c912f16c42c8f15dc6b7e6c8f"
ARC_COMMIT = "399030444e0ab0cc8b4e199870fb20b863846f34"
DOMAINS = ("scan_compositional_language", "arc_visual_transformation")
PER_DOMAIN_TRAIN = 2
PER_DOMAIN_TARGET = 4

def canon(x):
    return json.dumps(x, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)

def sha(x):
    return hashlib.sha256(x if isinstance(x, bytes) else x.encode()).hexdigest()

def load(p):
    return json.loads(Path(p).read_text())

def write(p, value):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(canon(value) + "\n")

def stable(domain, identifier):
    return sha(SALT + "/" + domain + "/" + str(identifier))

def parse_scan(path):
    rows = []
    for i, line in enumerate(Path(path).read_text().splitlines()):
        m = re.fullmatch(r"IN: (.*?) OUT: (.*)", line.strip())
        if m is None:
            raise ValueError("SCAN official source format changed at line " + str(i))
        rows.append({"id": sha(m.group(1))[:20], "input": m.group(1), "output": m.group(2)})
    if len(rows) < 1000 or len({r["input"] for r in rows}) != len(rows):
        raise ValueError("SCAN original corpus too small or duplicate")
    return rows

def arc_rows(path):
    rows = []
    for p in Path(path).glob("*.json"):
        task = load(p)
        train = task.get("train", [])
        test = task.get("test", [])
        if len(train) < 3 or len(test) != 1 or "output" not in test[0]:
            continue
        # Filter by declared SOURCE visual complexity only, never target label.
        if sum(len(row) for pair in train[:3] for key in ("input", "output")
               for row in pair[key]) > 160:
            continue
        if sum(len(row) for row in test[0]["input"]) > 70:
            continue
        rows.append({"id": p.stem, "train": train, "test": test})
    if len(rows) < 6:
        raise ValueError("ARC fixed-size eligible cohort unexpectedly missing")
    return rows

def episode(domain, task_id, mechanism, demonstration, probe, sealed, target=None):
    value = {
        "domain": domain, "task_id": task_id, "mechanism": mechanism,
        "demonstration": demonstration,
        "queries": {"probe": probe["input"], "sealed": sealed["input"]},
        "sealed_ids": ["sealed"],
        "source_identity": sha(domain + "/" + task_id),
    }
    if target is not None:
        value["queries"]["target"] = target["input"]
    oracle = {"task_id": task_id, "source_identity": value["source_identity"],
              "mechanism": mechanism,
              "probe": {"input": probe["input"], "output": probe["output"]},
              "sealed": {"input": sealed["input"], "output": sealed["output"]}}
    return value, oracle

def freeze(scan_train, scan_test, arc_dir, out_dir):
    a = sorted(parse_scan(scan_train), key=lambda x: stable("scan/source", x["id"]))
    b = sorted(parse_scan(scan_test), key=lambda x: stable("scan/target", x["id"]))
    arc = sorted(arc_rows(arc_dir), key=lambda x: stable("arc/task", x["id"]))
    if {x["input"] for x in a}.intersection(x["input"] for x in b):
        raise ValueError("SCAN official train/test input overlap")
    visible = {"schema": "NEUMANN.Q3Q6.FINAL.SAME-WORLD.VISIBLE.v1",
               "study": SALT, "training": [], "evaluation": [],
               "source_memory": [], "model_revision": REV,
               "source_commits": {"SCAN": SCAN_COMMIT, "ARC": ARC_COMMIT}}
    oracle = {}
    gold = {}
    # SCAN SOURCE observations and all SCAN TEST examples are from the
    # same original-author compositional instruction semantics.
    scan_world = "author-original/SCAN/grammar@" + SCAN_COMMIT
    for i in range(2):
        start = i * 3
        task, src = episode(DOMAINS[0], "SCAN-train-" + str(i),
                            scan_world, a[start], a[start+1], a[start+2])
        visible["training"].append(task)
        oracle[task["task_id"]] = src
        for sample in (a[start], a[start+1]):
            visible["source_memory"].append(
                {"domain": DOMAINS[0], "source_task_id": task["task_id"],
                 "query": sample["input"], "observed": sample["output"],
                 "scope": "TRUSTED_SOURCE_ONLY", "mechanism": scan_world})
    for i in range(PER_DOMAIN_TARGET):
        task, src = episode(DOMAINS[0], "SCAN-eval-" + str(i),
                            scan_world, a[6], a[7], a[8], b[i])
        visible["evaluation"].append(task)
        oracle[task["task_id"]] = src
        gold[task["task_id"]] = b[i]["output"]

    # Each ARC puzzle defines its OWN latent transformation. Its demonstration,
    # probe, sealed source and heldout target all belong to that SAME puzzle.
    # Different puzzle rules require the common discovery policy to generalize.
    for i, puzzle in enumerate(arc[:PER_DOMAIN_TRAIN+PER_DOMAIN_TARGET]):
        mechanism = "author-original/ARC/puzzle/" + puzzle["id"]
        task_id = "ARC-" + ("train-" if i < 2 else "eval-") + puzzle["id"]
        demo, probe, sealed = puzzle["train"][:3]
        is_eval = i >= 2
        task, src = episode(DOMAINS[1], task_id, mechanism, demo, probe, sealed,
                            puzzle["test"][0] if is_eval else None)
        oracle[task_id] = src
        if is_eval:
            visible["evaluation"].append(task)
            gold[task_id] = puzzle["test"][0]["output"]
        else:
            visible["training"].append(task)
            for pair in (demo, probe):
                visible["source_memory"].append(
                    {"domain": DOMAINS[1], "source_task_id": task["task_id"],
                     "query": pair["input"],
                     "observed": pair["output"],
                     "scope": "TRUSTED_SOURCE_ONLY", "mechanism": mechanism})
    if (len(visible["training"]) != 4 or len(visible["evaluation"]) != 8
            or len(gold) != 8 or len(oracle) != 12):
        raise AssertionError("precommitted 4 SOURCE gradients + 8 TARGETs changed")
    for t in visible["training"] + visible["evaluation"]:
        assert "output" not in t["queries"]
        assert set(t["queries"]) in ({"probe","sealed"},{"probe","sealed","target"})
        assert t["mechanism"] == oracle[t["task_id"]]["mechanism"]
    write(Path(out_dir) / "visible/visible.json", visible)
    write(Path(out_dir) / "source/source.json", oracle)
    write(Path(out_dir) / "gold/gold.json", gold)
    manifest = {"study": SALT, "selection": "SHA-ID ONLY, never using target label",
                "target_count": 8, "source_training_episodes": 4,
                "same_hidden_world_source_probe_sealed_target": True,
                "target_labels_in_visible": False,
                "visible_hash": sha((Path(out_dir)/"visible/visible.json").read_bytes()),
                "source_hash": sha((Path(out_dir)/"source/source.json").read_bytes()),
                "original_target_id_hashes": [sha(t["task_id"]) for t in visible["evaluation"]],
                "original_authors": ["Brenden Lake et al. SCAN", "Francois Chollet ARC-AGI"]}
    write(Path(out_dir) / "visible/manifest.json", manifest)
    print("FROZEN_SAME_WORLD_SOURCE_AND_TARGET_IDENTITIES", canon(manifest), flush=True)

class PolicyView:
    def __init__(self, model, memory, train):
        self.model, self.memory, self.train = model, tuple(memory), train
    def hypotheses(self, context, history, queries):
        return self.model.hypotheses(context, self.memory + tuple(history), queries)
    def learn_from_counterexample(self, events):
        return self.model.learn_from_counterexample(events) if self.train else None
    def learn_grounded_source_without_hypothesis(self, **kwargs):
        return self.model.learn_grounded_source_without_hypothesis(**kwargs) if self.train else None

def verifier(task, oracle):
    entry = oracle[task["task_id"]]
    def check(identity, query_id, query, observed, evidence_id):
        row = entry.get(query_id, {})
        return bool(identity == entry["source_identity"] and
                    evidence_id == identity + "/" + query_id + "/SIGNED-SOURCE"
                    and canon(row.get("input")) == canon(query)
                    and canon(row.get("output")) == canon(observed))
    return check

def effort(model, task, oracle, memory, training):
    core = CausalExperienceCore(PolicyView(model, memory, training),
                                max_hypotheses=2, max_experiences=32)
    context = {"original_author_semantics": task["domain"],
               "source_demonstration": task["demonstration"],
               "mechanism_identity": task["mechanism"],
               "instruction": "Discover a falsifiable latent relation from this SAME world; "
                              "probe may refute your hypothesis; then revise it."}
    bindings = {qid: task["mechanism"] for qid in task["queries"]}
    initial, revised, receipt, certified, raw, submitted = (None,)*6
    certified = False
    status = "ABSTAIN"
    start = time.monotonic()
    try:
        core.start(task["source_identity"], context, task["queries"],
                   sealed_queries=("sealed",), episode_bindings=bindings,
                   allow_grounded_bootstrap=training)
        initial = core.hypotheses[0].digest if core.hypotheses else None
        e = oracle[task["task_id"]]
        updates = core.observe("probe", e["probe"]["output"],
                    evidence_id=task["source_identity"]+"/probe/SIGNED-SOURCE",
                    verify_source=verifier(task,oracle))
        receipt = updates[0].learning_receipt
        core.revise(context)
        revised = core.hypotheses[0].digest if core.hypotheses else None
        core.freeze()
        certified = core.certify_sealed_source(
                    "sealed", e["sealed"]["output"],
                    evidence_id=task["source_identity"]+"/sealed/SIGNED-SOURCE",
                    verify_source=verifier(task, oracle))
        if not training and core.hypotheses:
            raw = core.hypotheses[0].predictions.get("target")
            submitted = raw if certified else None
        status = "SOURCE_CERTIFIED" if certified else "ABSTAIN_SOURCE_REFUTED"
    except (ValueError, KeyError, RuntimeError, TypeError) as ex:
        status = "ABSTAIN_" + type(ex).__name__
    return {"task_id": task["task_id"], "domain": task["domain"],
            "source_certified": certified,
            "initial_latent_sha256": initial, "revised_latent_sha256": revised,
            "genuinely_changed_latent": bool(revised and initial != revised),
            "learning_receipt": receipt,
            "raw_prediction": raw, "certified_prediction": submitted,
            "status": status, "seconds": round(time.monotonic()-start, 3),
            "original_TARGET_gold_seen": False}

def source_nearest(domain, query, task, memory, oracle):
    refs = [x for x in memory if x["domain"] == domain]
    refs += [{"query": task["demonstration"]["input"],
              "observed": task["demonstration"]["output"]}]
    row = oracle[task["task_id"]]["probe"]
    refs.append({"query": row["input"], "observed": row["output"]})
    if domain == DOMAINS[0]:
        qt = set(re.findall(r"\w+", str(query).lower()))
        ranked = sorted(enumerate(refs), key=lambda ix:
            (-(len(qt & set(re.findall(r"\w+",str(ix[1]["query"]).lower()))) /
               max(1, len(qt | set(re.findall(r"\w+",str(ix[1]["query"]).lower()))))), ix[0]))
        return ranked[0][1]["observed"]
    # Transparent classical nearest input-grid baseline, not an ARC expert.
    def distance(a, b):
        return abs(len(a)-len(b))*20 + sum(
            abs(len(x)-len(y))*10 + sum(p != q for p,q in zip(x,y))
            for x,y in zip(a,b))
    return min(refs, key=lambda e: distance(e["query"],query))["observed"]

def infer(visible_path, source_path, out):
    visible, oracle = load(visible_path), load(source_path)
    if visible["schema"] != "NEUMANN.Q3Q6.FINAL.SAME-WORLD.VISIBLE.v1":
        raise ValueError("visible precommit invalid")
    if len(visible["training"]) != 4 or len(visible["evaluation"]) != 8:
        raise ValueError("source and target experiment budget changed")
    if set(oracle) != {x["task_id"] for x in visible["training"]+visible["evaluation"]}:
        raise ValueError("SOURCE checker IDs mismatch")
    if any("output" in t["queries"].get("target", {}) for t in visible["evaluation"]):
        raise ValueError("TARGET leaked")
    results = {"A":[], "B":[], "C":[]}
    training_receipts=[]
    weight_updates, weight_delta = 0, 0.0
    for arm in ("A","B","C"):
        model=TrainableLatentWorldPolicy(revision=REV,max_new_tokens=500,
                  max_context_tokens=4096, max_updates=4, seed=1007)
        if arm=="C":
            for t in visible["training"]:
                row=effort(model,t,oracle,
                           [m for m in visible["source_memory"]
                            if m["domain"]==t["domain"] and
                            m["source_task_id"]!=t["task_id"]],True)
                training_receipts.append(row)
                print("FINAL_Q3Q6_TRAIN_SOURCE_ONLY",t["task_id"],
                      row["status"], "updates",model.update_count,flush=True)
            weight_updates=model.update_count
            weight_delta=sum(float(r["learning_receipt"].get(
                "actual_trainable_weight_delta_l1",0))
                for r in training_receipts if isinstance(r["learning_receipt"],dict))
        for t in visible["evaluation"]:
            memory = ([m for m in visible["source_memory"]
                       if m["domain"]==t["domain"]] if arm != "A" else [])
            record = effort(model,t,oracle,memory,False)
            record["classical_source_only_prediction"] = source_nearest(
                t["domain"],t["queries"]["target"],t,
                [m for m in visible["source_memory"] if m["domain"]==t["domain"]],oracle)
            results[arm].append(record)
            print("FINAL_Q3Q6_FROZEN_TARGET",arm,t["task_id"],record["status"],
                  "target_gold_read",False,flush=True)
        del model
        gc.collect()
    receipt = {"schema":"NEUMANN.Q3Q6.FINAL.FROZEN.v1",
               "study":SALT,"model_revision":REV,
               "visible_sha256":sha(Path(visible_path).read_bytes()),
               "source_sha256":sha(Path(source_path).read_bytes()),
               "A_B_C":results, "C_source_training_receipts":training_receipts,
               "C_actual_weight_updates":weight_updates,"C_weight_delta_l1":weight_delta,
               "same_model_weights_start":True,"B_C_same_source_memory":True,
               "TARGET_gold_read":False,
               "no_specialized_answer_generator":True}
    write(out,receipt)
    print("FINAL_Q3Q6_PREDICTIONS_SHA_FROZEN",sha(Path(out).read_bytes()),flush=True)

def score(pred_path, gold_path, out):
    pred, gold = load(pred_path), load(gold_path)
    if pred["schema"] != "NEUMANN.Q3Q6.FINAL.FROZEN.v1" or len(gold)!=8:
        raise ValueError("gold/model contract broken")
    by_arm = {}
    for arm in ("A","B","C"):
        values = {}
        for r in pred["A_B_C"][arm]:
            tid = r["task_id"]
            if tid not in gold or tid in values:
                raise ValueError("missing or duplicate original")
            values[tid] = {
                "exact_certified": bool(r["source_certified"] and
                         r["certified_prediction"] is not None and
                         canon(r["certified_prediction"]) == canon(gold[tid])),
                "exact_raw": (r["raw_prediction"] is not None and
                              canon(r["raw_prediction"]) == canon(gold[tid])),
                "classical_correct": (canon(r["classical_source_only_prediction"]) ==
                                      canon(gold[tid])),
                "changed_latent": r["genuinely_changed_latent"]}
        by_arm[arm] = values
    domain_stats = {}
    for domain in DOMAINS:
        rows = [r for r in pred["A_B_C"]["C"] if r["domain"]==domain]
        wins = [r["task_id"] for r in rows
                if by_arm["C"][r["task_id"]]["exact_certified"]
                and by_arm["C"][r["task_id"]]["changed_latent"]
                and not by_arm["B"][r["task_id"]]["exact_certified"]
                and not by_arm["C"][r["task_id"]]["classical_correct"]]
        domain_stats[domain] = {
            "cases": len(rows),
            "A_certified": sum(by_arm["A"][r["task_id"]]["exact_certified"] for r in rows),
            "B_certified": sum(by_arm["B"][r["task_id"]]["exact_certified"] for r in rows),
            "C_certified": sum(by_arm["C"][r["task_id"]]["exact_certified"] for r in rows),
            "A_raw": sum(by_arm["A"][r["task_id"]]["exact_raw"] for r in rows),
            "B_raw": sum(by_arm["B"][r["task_id"]]["exact_raw"] for r in rows),
            "C_raw": sum(by_arm["C"][r["task_id"]]["exact_raw"] for r in rows),
            "classical_correct": sum(by_arm["C"][r["task_id"]]["classical_correct"] for r in rows),
            "C_exclusive_new_concept_source_certified_ids":wins}
    required = pred["C_actual_weight_updates"] > 0 and pred["C_weight_delta_l1"]>0
    minimal = required and all(domain_stats[d]["C_exclusive_new_concept_source_certified_ids"]
                               for d in DOMAINS)
    verdict = "MINIMAL_EVIDENCE_ONLY_NOT_GLOBAL_PASS" if minimal else "NO_STOP"
    report={"study":SALT, "verdict":verdict,
            "question_answer":"미정" if minimal else "아니오",
            "C_weight_updates":pred["C_actual_weight_updates"],
            "C_weight_delta_l1":pred["C_weight_delta_l1"],
            "domains":domain_stats,
            "caveats":["not independent reproduction",
                        "classical nearest SOURCE is not a strong domain specialist",
                        "possible pretrained benchmark contamination",
                        "within-task discovered mechanism not identified by label alone",
                        "no global Q3/Q6 or 10x compute PASS"]}
    write(out,report)
    print("FINAL_Q3Q6_SCIENTIFIC_VERDICT",canon(report),flush=True)

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="cmd",required=True)
    f=sub.add_parser("freeze")
    for x in ("scan-train","scan-test","arc-dir","out-dir"):
        f.add_argument("--"+x,required=True)
    i=sub.add_parser("infer")
    for x in ("visible","source","out"):
        i.add_argument("--"+x,required=True)
    s=sub.add_parser("score")
    for x in ("pred","gold","out"):
        s.add_argument("--"+x,required=True)
    a=p.parse_args()
    if a.cmd=="freeze": freeze(a.scan_train,a.scan_test,a.arc_dir,a.out_dir)
    if a.cmd=="infer": infer(a.visible,a.source,a.out)
    if a.cmd=="score": score(a.pred,a.gold,a.out)
if __name__=="__main__": main()
