"""NEUMANN P1.12 | First fixed-revision joint cross-encoder test on 12 new opened tasks.

A micro semantic-selector diagnostic only. NOT autonomous new operation
invention, frontier-level solving, unseen-family transfer, or 10x efficiency.
The previously frozen v1 record contained one wrong reference label; do not
overwrite it. Use the preregistered corrected-v2 source and exact source SHA.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256, sha1
import json
from pathlib import Path
from time import perf_counter_ns

from neumann1.control_plane_p112 import (
    MODEL, build_joint_pairs, select_unique_top, FrozenMiniLMCrossEncoder
)

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "docs/experiments/control_plane_p112_FRESH_FIRST_CORRECTED_FROZEN.json"
LOCK_FILE = ROOT / "docs/experiments/control_plane_p112_FIRST_SOURCE_LOCK.json"
SCHEMA = "neumann.p112.fresh-semantic-first-model.v1"
LETTERS = "ABCD"


def git_blob(path):
    data = Path(path).read_bytes()
    return sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load_frozen():
    data = json.loads(DATA_FILE.read_text())
    lock = json.loads(LOCK_FILE.read_text())
    if git_blob(DATA_FILE) != lock["dataset_blob_sha"]:
        raise ValueError("DATASET_INTEGRITY_DRIFT")
    for relative, expected in lock["source_blobs"].items():
        if git_blob(ROOT / relative) != expected:
            raise ValueError("SOURCE_INTEGRITY_DRIFT: " + relative)
    if data["model_id"] != MODEL["model_id"] or data["model_revision"] != MODEL["model_revision"]:
        raise ValueError("MODEL_IDENTITY_DRIFT")
    if data["expected_parameters"] != MODEL["expected_parameters"]:
        raise ValueError("MODEL_PARAMETERS_DRIFT")
    if len(data["tasks"]) != 12 or len({t["id"] for t in data["tasks"]}) != 12:
        raise ValueError("COHORT_NOT_TWELVE_UNIQUE")
    if data["raw_top_min_correct"] != 9 or data["additional_correct_over_best_lexical_min"] != 2:
        raise ValueError("POSTREG_GATE_CHANGE")
    return data, lock


def public_ir(row):
    if set(row) != {"id", "target_role", "candidate_roles", "expected_index"}:
        raise ValueError("ONLY_FIXED_TASK_FIELDS")
    roles = row["candidate_roles"]
    if len(roles) != 4 or len(set(roles)) != 4:
        raise ValueError("NEED_FOUR_UNIQUE_ROLES")
    if not 0 <= row["expected_index"] < 4:
        raise ValueError("INVALID_LABEL")
    declarations = [f"{LETTERS[i]} is the {role}" for i, role in enumerate(roles)]
    instruction = ", ".join(declarations[:3]) + ", and " + declarations[3] + ". "
    instruction += "Resolve 'It' to the " + row["target_role"] + ", then return a complete assignment."
    ir = build_joint_pairs(instruction, list(LETTERS))
    if ir["target_role"] != row["target_role"] or [x["candidate_text"] for x in ir["pairs"]] != [
        "Candidate role: " + x for x in roles
    ]:
        raise ValueError("SOURCE_ROLE_IR_DRIFT")
    return ir


def lexical_guesses(rows):
    """Untrained no-label comparator. Input text and candidate vocab only."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    out = {"word": [], "char": [], "constant_first": []}
    for row in rows:
        ir = public_ir(row)
        queries = [ir["pairs"][0]["query"]]
        candidates = [v["candidate_text"] for v in ir["pairs"]]
        text = queries + candidates
        for key, opts in (
            ("word", {"analyzer": "word", "ngram_range": (1, 2)}),
            ("char", {"analyzer": "char", "ngram_range": (2, 5)}),
        ):
            vec = TfidfVectorizer(**opts).fit_transform(text)
            scores = cosine_similarity(vec[:1], vec[1:]).ravel().tolist()
            order = sorted(range(4), key=lambda i: -scores[i])
            winner = None if scores[order[0]] == scores[order[1]] else order[0]
            out[key].append({"winner": winner, "scores": scores})
        out["constant_first"].append({"winner": 0, "scores": None})
    return out


def first_actual():
    started = perf_counter_ns()
    data, lock = load_frozen()
    rows = data["tasks"]
    # The existing reference labels are deliberately excluded from model inputs.
    baselines = lexical_guesses(rows)
    model_started = perf_counter_ns()
    selector = FrozenMiniLMCrossEncoder(device="cpu")
    startup_ms = (perf_counter_ns() - model_started) / 1e6
    attempts = []
    for row in rows:
        ir = public_ir(row)
        t0 = perf_counter_ns()
        output = selector.score(ir)
        item_wall_ms = (perf_counter_ns() - t0) / 1e6
        if output.get("forward_calls") != 1 or output["input_rows"] != 4:
            raise ValueError("FROZEN_SINGLE_FORWARD_CONTRACT")
        logits = output["logits"]
        if len(logits) != 4:
            raise ValueError("INCORRECT_SCORE_SHAPE")
        try:
            selection = select_unique_top(ir, logits)
            candidate = selection["selected_candidate_position"]
            status = "UNIQUE_TOP"
        except ValueError:
            candidate = None
            status = "ABSTAIN"
        attempts.append({
            "id": row["id"],
            "public_ir_sha256": sha256(canonical(ir).encode()).hexdigest(),
            "raw_candidate": candidate,
            "model_logits": logits,
            "forward_calls": 1,
            "input_tokens": output["input_tokens"],
            "padded_tokens": output["padded_tokens"],
            "item_wall_ms": item_wall_ms,
            "status": status,
        })
    # The original label is not touched until every model ranking has been emitted.
    gold = [r["expected_index"] for r in rows]
    cross_correct = sum(a["raw_candidate"] == gt for a, gt in zip(attempts, gold))
    baseline_counts = {
        name: sum(p["winner"] == gt for p, gt in zip(preds, gold))
        for name, preds in baselines.items()
    }
    strongest_lexical = max(baseline_counts.values())
    for i, row in enumerate(rows):
        attempts[i]["gold_index"] = gold[i]
        attempts[i]["correct"] = attempts[i]["raw_candidate"] == gold[i]
        attempts[i]["lexical_guesses"] = {
            name: baselines[name][i]["winner"] for name in baselines
        }
    result_pass = (cross_correct >= 9
                   and cross_correct - strongest_lexical >= 2
                   and selector.forward_calls == len(rows))
    report = {
        "schema": SCHEMA,
        "dataset_source_git_blob": lock["dataset_blob_sha"],
        "source_lock_sha256": sha256(LOCK_FILE.read_bytes()).hexdigest(),
        "reference_revision": MODEL["model_revision"],
        "actual_pretrained_model_loaded": True,
        "model_id": MODEL["model_id"],
        "parameter_count": MODEL["expected_parameters"],
        "device": "cpu",
        "model_training": False,
        "self_supervised_program_invention": False,
        "inference_inputs_exclude_gold": True,
        "previous_p111_eval_reused": False,
        "status": "P112_LOCAL_OPENED_PASS" if result_pass else "P112_LOCAL_OPENED_FAIL",
        "explanation": "A fresh author-constructed semantic ranker diagnostic, not a general reasoning or Q3 discovery result.",
        "scores": {
            "N": len(rows),
            "cross_correct": cross_correct,
            "best_lexical_correct": strongest_lexical,
            "lexical_baselines": baseline_counts,
            "extra_correct_vs_best_lexical": cross_correct - strongest_lexical,
            "actual_forward_calls": selector.forward_calls,
            "load_ms": startup_ms,
            "study_ms": (perf_counter_ns() - started)/1e6,
            "inputs_tokens": sum(x["input_tokens"] for x in attempts),
            "padded_tokens": sum(x["padded_tokens"] for x in attempts),
            "power_joules": None,
            "money_usd": None,
            "accelerator_vram_bytes": None
        },
        "conclusion": ("Admit only new independent validation, not Q1-Q7 closure."
                       if result_pass else
                       "Stop this raw MS-MARCO relevance primitive as a semantic judge; do not tune on this opened set."),
        "Q1_Q7": "OPEN",
        "rows": attempts,
    }
    return report


if __name__ == "__main__":
    print(json.dumps(first_actual(), ensure_ascii=False, indent=2))
