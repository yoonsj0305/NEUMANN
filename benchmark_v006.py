from __future__ import annotations
import json
import numpy as np
from sklearn.metrics import brier_score_loss, roc_auc_score

from neumann1 import TwoStageOpenSetStructureFormer, training_examples, IRKind
from neumann1.prototype_open_set import PrototypeOpenSetStructureFormer
from neumann1.open_set_v006_dataset import validation_v006, final_test_v006


def expected_calibration_error(y_true, probs, bins=5):
    y_true = np.asarray(y_true, dtype=float)
    probs = np.asarray(probs, dtype=float)
    edges = np.linspace(0, 1, bins + 1)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (probs >= lo) & (probs < hi if hi < 1 else probs <= hi)
        if not mask.any():
            continue
        conf = probs[mask].mean()
        acc = y_true[mask].mean()
        ece += mask.mean() * abs(conf - acc)
    return float(ece)


def selective_curve(score_fn, predict_label_fn, examples, thresholds):
    rows = []
    known = [x for x in examples if x[1] != IRKind.UNKNOWN]
    unknown = [x for x in examples if x[1] == IRKind.UNKNOWN]
    for th in thresholds:
        known_routed = 0
        known_wrong = 0
        unknown_routed = 0
        for text, expected, _ in known:
            score = score_fn(text)
            if score >= th:
                known_routed += 1
                if predict_label_fn(text) != expected:
                    known_wrong += 1
        for text, _, _ in unknown:
            if score_fn(text) >= th:
                unknown_routed += 1
        rows.append({
            "threshold": round(float(th), 4),
            "known_coverage": known_routed / len(known),
            "selective_risk_known": known_wrong / known_routed if known_routed else 0.0,
            "unknown_false_route_rate": unknown_routed / len(unknown),
        })
    return rows


def evaluate_model(name, model, test, score_fn, threshold):
    rows = []
    for text, expected, bucket in test:
        predicted, confidence = model.predict_kind(text)
        score = score_fn(text)
        rows.append({
            "text": text,
            "expected": expected.value,
            "bucket": bucket,
            "predicted": predicted.value,
            "correct": predicted == expected,
            "knownness_score": score,
            "reported_confidence": confidence,
        })
    known = [r for r in rows if r["expected"] != "unknown"]
    unknown = [r for r in rows if r["expected"] == "unknown"]
    near = [r for r in rows if r["bucket"] == "near_unknown"]
    routed_known = [r for r in known if r["predicted"] != "unknown"]
    return {
        "name": name,
        "threshold": float(threshold),
        "n": len(rows),
        "accuracy": sum(r["correct"] for r in rows) / len(rows),
        "known_auto_route_coverage": len(routed_known) / len(known),
        "routed_known_precision": sum(r["correct"] for r in routed_known) / max(1, len(routed_known)),
        "unknown_false_route_rate": sum(r["predicted"] != "unknown" for r in unknown) / len(unknown),
        "near_unknown_false_route_rate": sum(r["predicted"] != "unknown" for r in near) / len(near),
    }, rows


def evaluate():
    train = training_examples()
    validation = validation_v006()
    test = final_test_v006()

    two = TwoStageOpenSetStructureFormer().fit(train)
    two_val = two.tune_threshold(validation)
    proto = PrototypeOpenSetStructureFormer().fit(train)
    proto_val = proto.tune_threshold(validation)

    two_summary, two_rows = evaluate_model(
        "two_stage_logistic", two, test, two.known_probability, two.threshold
    )
    proto_summary, proto_rows = evaluate_model(
        "prototype_centroid", proto, test, lambda text: proto.score(text)[1], proto.threshold
    )

    y = [1 if expected != IRKind.UNKNOWN else 0 for _, expected, _ in test]
    p_two = [two.known_probability(text) for text, _, _ in test]
    s_proto = [proto.score(text)[1] for text, _, _ in test]
    diagnostics = {
        "two_stage_brier": float(brier_score_loss(y, p_two)),
        "two_stage_ece_5bin": expected_calibration_error(y, p_two, bins=5),
        "two_stage_knownness_auroc": float(roc_auc_score(y, p_two)),
        "prototype_similarity_auroc": float(roc_auc_score(y, s_proto)),
    }

    curves = {
        "two_stage": selective_curve(
            two.known_probability,
            two.predict_supported_kind,
            test,
            np.linspace(0.25, 0.85, 13),
        ),
        "prototype": selective_curve(
            lambda text: proto.score(text)[1],
            lambda text: proto.score(text)[0],
            test,
            np.linspace(0.05, 0.65, 13),
        ),
    }

    return {
        "notes": [
            "v0.0.6 focuses on structurally-near OOD rejection, not full IR generation.",
            "Thresholds are tuned on validation_v006 and frozen before final_test_v006.",
            "Datasets are tiny hand-authored research fixtures; rates are descriptive, not statistical guarantees.",
        ],
        "validation": {
            "two_stage": two_val.__dict__,
            "prototype": proto_val.__dict__,
        },
        "summary": {
            "two_stage": two_summary,
            "prototype": proto_summary,
            "diagnostics": diagnostics,
        },
        "selective_curves": curves,
        "rows": {"two_stage": two_rows, "prototype": proto_rows},
    }


if __name__ == "__main__":
    result = evaluate()
    print(json.dumps(result["summary"], indent=2))
    with open("benchmark_v006_results.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)