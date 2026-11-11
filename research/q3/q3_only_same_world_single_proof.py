"""ONE scoped Q3-only causal-invention study; NO cross-domain Q6.

Decision that changes whichever way this goes:
  strict witnessed hypothesis discovery with causal ablation -> retain Q3
  neural proposal mechanism for independent replication;
  otherwise -> STOP this neural mechanism instead of a fourth tweak.

Only one small human-created causal world (NOT original-author independent),
one verified SOURCE intervention, one separately sealed SOURCE check.
The mechanism/oracle is NOT in the model-visible input and the score job alone
can access sealed gold. This is at most a limited, within-world Q3 proof.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

STUDY = "NEUMANN.Q3.ONLY.CAUSAL.WORLD.2026-11-11.FROZEN"
MODEL_REV = "ea3f2471cf1b1f0db85067f1ef93848e38e88c25"


def canon(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False)


def digest(value):
    return sha256((value if isinstance(value, bytes)
                   else canon(value).encode())).hexdigest()


def save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canon(obj) + "\n")


def read(path):
    return json.loads(Path(path).read_text())


def _hidden_causal_world(query):
    """Scorer/SOURCE-oracle only, NEVER passed to model in a prompt."""
    a, b, signal = query["a"], query["b"], query["signal"]
    if signal == "raven":
        return a + b
    if signal == "cobalt":
        return a * b
    if signal == "ember":
        return abs(a - b)
    raise ValueError("unknown intervention")


def freeze(output):
    # These intervention IDs and values are frozen once; no adaptive tuning
    # on independent sealed observations or original benchmark outputs.
    source_examples = [
        {"input": {"signal": "raven", "a": 2, "b": 3}, "observed": 5},
        {"input": {"signal": "raven", "a": 4, "b": 2}, "observed": 6},
        {"input": {"signal": "cobalt", "a": 2, "b": 3}, "observed": 6},
        {"input": {"signal": "cobalt", "a": 3, "b": 4}, "observed": 12},
    ]
    assert all(_hidden_causal_world(e["input"]) == e["observed"]
               for e in source_examples)
    probe = {"signal": "ember", "a": 9, "b": 4}
    sealed = {"signal": "ember", "a": 8, "b": 5}
    if probe == sealed or sealed in [x["input"] for x in source_examples]:
        raise ValueError("sealed query overlaps any SOURCE demonstration")
    mechanism = digest({"study": STUDY, "episode": "world-1"})
    visible = {
        "study": STUDY,
        "mechanism": mechanism,
        "context": {
            "observed_same_world_causal_interventions": source_examples,
            "instruction": (
                "Infer a new latent rule from SOURCE only. The unknown "
                "observable relation can vary by signal. Predict the "
                "registered intervention values; revise the invented "
                "hypothesis after a verified counterexample."
            ),
        },
        "queries": {"probe": probe, "sealed": sealed},
        "sealed_ids": ["sealed"],
        "target_labels_present": False,
        "model_revision": MODEL_REV,
    }
    source = {"probe": {"input": probe,
                        "observed": _hidden_causal_world(probe),
                        "evidence_id": mechanism + "/probe/SIGNED-SOURCE"}}
    gold = {"sealed": {"input": sealed,
                       "observed": _hidden_causal_world(sealed)}}
    base = Path(output)
    save(base / "visible/visible.json", visible)
    save(base / "source/source.json", source)
    save(base / "gold/gold.json", gold)
    save(base / "visible/manifest.json", {
        "study": STUDY, "visible_sha256": digest(
            (base / "visible/visible.json").read_bytes()),
        "source_sha256": digest((base / "source/source.json").read_bytes()),
        "sealed_identity_sha256": digest(sealed),
        "sealed_gold_not_model_visible": True,
        "world_count": 1, "neural_gradient_cap": 1,
        "original_author_independent": False,
    })
    print("Q3_ONLY_PRECOMMITTED_ONE_HIDDEN_WORLD", 
          (base / "visible/manifest.json").read_text().strip(), flush=True)


class PolicyView:
    def __init__(self, policy, training):
        self.policy = policy
        self.training = training

    def hypotheses(self, context, history, queries):
        return self.policy.hypotheses(context, history, queries)

    def learn_from_counterexample(self, events):
        return (self.policy.learn_from_counterexample(events)
                if self.training else None)


def infer(visible_path, source_path, output):
    from neumann1.causal_experience import CausalExperienceCore
    from neumann1.q3_latent_world_policy import (
        TrainableLatentWorldPolicy, QUERY_SYSTEM, _chat
    )
    visible, source = read(visible_path), read(source_path)
    if visible["study"] != STUDY or source["probe"]["input"] != visible["queries"]["probe"]:
        raise ValueError("broken frozen SOURCE contract")
    if visible["target_labels_present"] or "observed" in visible["queries"]["sealed"]:
        raise ValueError("sealed SOURCE label leaked")
    result = {"study": STUDY, "model_revision": MODEL_REV,
              "original_sealed_gold_seen": False,
              "synthetic_single_world_not_Q6": True,
              "arms": {}}

    for arm in ("B_context_only", "C_source_gradient"):
        policy = TrainableLatentWorldPolicy(
            revision=MODEL_REV, max_new_tokens=128,
            max_context_tokens=4096, max_updates=1, seed=1007)
        core = CausalExperienceCore(PolicyView(policy, arm.startswith("C_")),
                                    max_hypotheses=1, max_experiences=4)
        binding = {k: visible["mechanism"] for k in visible["queries"]}
        record = {"arm": arm, "status": "INCOMPLETE"}
        try:
            core.start(visible["mechanism"], visible["context"],
                       visible["queries"], sealed_queries=("sealed",),
                       episode_bindings=binding)
            initial = core.hypotheses[0]
            selected = core.select_query()
            if selected != "probe":
                raise ValueError("model failed to select own SOURCE falsification")

            def verifier(task_id, query_id, query, observed, evidence_id):
                p = source["probe"]
                return (task_id == visible["mechanism"] and
                        query_id == "probe" and
                        canon(query) == canon(p["input"]) and
                        canon(observed) == canon(p["observed"]) and
                        evidence_id == p["evidence_id"])

            updates = core.observe(
                selected, source["probe"]["observed"],
                evidence_id=source["probe"]["evidence_id"],
                verify_source=verifier)
            core.revise(visible["context"])
            revised = core.hypotheses[0]
            if revised.digest == initial.digest:
                changed = False
            else:
                changed = True
            # Freeze all model weights before recording sealed-source prediction.
            core.freeze()
            record.update({
                "status": "FROZEN",
                "initial_model_concept": initial.latent_variables.get(
                    "proposed_internal_causal_concept"),
                "revised_model_concept": revised.latent_variables.get(
                    "proposed_internal_causal_concept"),
                "initial_model_hypothesis_sha": initial.digest,
                "revised_model_hypothesis_sha": revised.digest,
                "changed_model_hypothesis": changed,
                "initial_sealed_prediction": initial.predictions.get("sealed"),
                "revised_sealed_prediction": revised.predictions.get("sealed"),
                "revision_fits_disclosed_probe": (
                    canon(revised.predictions.get("probe")) ==
                    canon(source["probe"]["observed"])),
                "source_probe_contradicted_initial": updates[0].contradicted,
                "source_verified": True,
                "learning_receipt": updates[0].learning_receipt,
                "real_weight_updates": policy.update_count,
            })
            if arm.startswith("C_"):
                # An extra no-concept prediction is an *ablation*, with
                # identical SOURCE context and weights. It opens no gold.
                prefix = _chat(
                    policy.tokenizer, QUERY_SYSTEM, canon({
                        "SOURCE_observations": visible["context"],
                        "prior_verified_SOURCE": policy._source_witnesses(
                            core.experiences),
                        "model_authored_hypothesis": "",
                        "single_authorized_query": {
                            "sealed": visible["queries"]["sealed"]},
                    }))
                raw = policy._generate(prefix, max_new_tokens=128)
                try:
                    noc = json.loads(raw)
                except (ValueError, TypeError):
                    noc = raw
                record["no_hypothesis_sealed_ablation"] = noc
        except (ValueError, TypeError, RuntimeError, KeyError) as ex:
            record["status"] = "ABSTAIN_" + type(ex).__name__
            record["error"] = str(ex)[:250]
        result["arms"][arm] = record
        print("Q3_ONLY_FROZEN", arm, record["status"],
              "source_verified", record.get("source_verified", False),
              "updated", record.get("real_weight_updates", 0),
              "gold_seen", False, flush=True)
        del core, policy

    save(output, result)
    print("Q3_ONLY_PREDICTIONS_SHA256_FROZEN", digest(
        Path(output).read_bytes()), flush=True)


def score(pred_path, gold_path, output):
    pred, gold = read(pred_path), read(gold_path)
    if pred["study"] != STUDY or set(gold) != {"sealed"}:
        raise ValueError("study identity mismatch")
    b, c = (pred["arms"][k] for k in
            ("B_context_only", "C_source_gradient"))
    actual = gold["sealed"]["observed"]
    correct = (lambda value: canon(value) == canon(actual))
    c_correct = c.get("status") == "FROZEN" and correct(
        c.get("revised_sealed_prediction"))
    b_correct = b.get("status") == "FROZEN" and correct(
        b.get("revised_sealed_prediction"))
    before_correct = correct(c.get("initial_sealed_prediction"))
    no_concept_correct = correct(c.get("no_hypothesis_sealed_ablation"))
    changed = bool(c.get("changed_model_hypothesis") and
                   c.get("initial_model_concept") and
                   c.get("revised_model_concept") and
                   c["initial_model_concept"] != c["revised_model_concept"])
    update = c.get("learning_receipt") or {}
    neural_learning = bool(c.get("real_weight_updates", 0) == 1 and
                           update.get("actual_trainable_weight_delta_l1", 0)>0)
    source = bool(c.get("source_verified") and
                  c.get("revision_fits_disclosed_probe") and
                  c.get("source_probe_contradicted_initial"))
    limited = bool(c_correct and changed and neural_learning and source)
    strict = bool(limited and not b_correct and
                  not before_correct and not no_concept_correct)
    verdict = {
        "study": STUDY,
        "question_answer": "예" if strict else ("미정" if limited else "아니오"),
        "strict_model_authored_concept_causally_useful_partial": strict,
        "weak_single_world_model_revision_evidence_only": limited,
        "C_revised_sealed_correct": c_correct,
        "B_context_only_sealed_correct": b_correct,
        "C_initial_sealed_correct": before_correct,
        "C_without_concept_sealed_correct": no_concept_correct,
        "C_new_model_hypothesis": changed,
        "C_actual_SOURCE_gradient": neural_learning,
        "C_initial_probe_refuted_and_revised_probe_consistent": source,
        "model_authored_revised_concept": c.get("revised_model_concept"),
        "caveats": [
            "One intentionally simple human-created causal world",
            "Not independent original-author generalization",
            "One sealed SOURCE observation cannot establish universal law",
            "A successful prediction may reuse pretrained arithmetic concepts",
            "No Q6, Q4 or global Q3 general intelligence claim",
        ],
    }
    save(output, verdict)
    print("Q3_ONLY_SCIENTIFIC_VERDICT", canon(verdict), flush=True)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    for mode, fields in [
        ("freeze", ("out_dir",)),
        ("infer", ("visible", "source", "out")),
        ("score", ("pred", "gold", "out")),
    ]:
        cmd = sub.add_parser(mode)
        for field in fields:
            cmd.add_argument("--" + field.replace("_", "-"), required=True)
    args = parser.parse_args()
    if args.mode == "freeze":
        freeze(args.out_dir)
    elif args.mode == "infer":
        infer(args.visible, args.source, args.out)
    else:
        score(args.pred, args.gold, args.out)


if __name__ == "__main__":
    main()
