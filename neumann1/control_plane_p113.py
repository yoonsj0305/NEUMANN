"""P1.13: task-aligned NLI residual judge; no import-time neural work."""
from __future__ import annotations

import math
from time import perf_counter_ns
from neumann1.control_plane_p111 import semantic_role_ir
from neumann1.control_plane_p17 import build_candidates
from neumann1.control_plane_p112 import build_joint_pairs

MODEL = {
    "model_id": "cross-encoder/nli-deberta-v3-base",
    "model_revision": "6c749ce3425cd33b46d187e45b92bbf96ee12ec7",
    "weight_sha256": "d8148c6d49e0a7925134294c56326c71fe0ab1dc390e37355e00c7efbb488afa",
    "expected_parameters": 184424451,
    "architecture": "DebertaV2ForSequenceClassification",
    "labels": {"contradiction": 0, "entailment": 1, "neutral": 2},
}


def build_bundle(view):
    if type(view) is not dict or set(view) != {"instruction", "public"}:
        raise ValueError("exact semantic view required")
    if type(view["public"]) is not dict or set(view["public"]) != {"query"}:
        raise ValueError("query-only public payload required")
    parsed = {"instruction": "Return a complete assignment.", "public": view["public"]}
    bundle = build_candidates(parsed)
    # Validate every semantic byte and complete entity coverage, without an
    # instruction whitelist or an answer-bearing role dictionary.
    from experiments.control_plane_p111_registration import semantic_ir_from_bundle
    semantic_ir_from_bundle(view, parsed, bundle, list(range(len(bundle["candidates"]))))
    return parsed, bundle


def pairs(ir, arm):
    if type(ir) is not dict or set(ir) != {"target_role", "candidates"}:
        raise ValueError("exact role IR required")
    target, candidates = ir["target_role"], ir["candidates"]
    # Reuse the bounded grammar validator to validate arbitrary future roles.
    if not isinstance(candidates, list) or not 2 <= len(candidates) <= 4:
        raise ValueError("2..4 candidates required")
    entities = [c["entity"] for c in candidates]
    if any(set(c) != {"entity", "role"} for c in candidates):
        raise ValueError("role-only candidate fields required")
    declaration = ", ".join(f"{c['entity']} is the {c['role']}" for c in candidates)
    instruction = f"{declaration}. Resolve 'It' to the {target}, then return a complete assignment."
    if semantic_role_ir(instruction, entities) != ir:
        raise ValueError("role IR grammar drift")
    if arm == "baseline":
        joint = build_joint_pairs(instruction, entities)
        return [(p["query"], p["candidate_text"]) for p in joint["pairs"]]
    if arm != "nli":
        raise ValueError("unknown registered arm")
    return [("The component performs this function: " + target + ".",
             "This component is a " + c["role"] + ".") for c in candidates]


def scores_from_logits(logits, arm):
    if type(logits) is not list or not 2 <= len(logits) <= 4:
        raise ValueError("complete 2..4 pair logits required")
    width = 3 if arm == "nli" else 1 if arm == "baseline" else 0
    if not width or any(type(row) is not list or len(row) != width or
            any(type(v) not in (int, float) or not math.isfinite(v) for v in row) for row in logits):
        raise ValueError("finite registered logit matrix required")
    # Equal monotonic ranking to binary entailment-vs-contradiction softmax;
    # use log-odds to avoid saturation-induced fake ties. Not confidence.
    return [float(r[1] - r[0]) if arm == "nli" else float(r[0]) for r in logits]


def select(scores):
    if (type(scores) is not list or not 2 <= len(scores) <= 4 or
            any(type(v) not in (int, float) or not math.isfinite(v) for v in scores)):
        raise ValueError("finite complete scores required")
    best = max(scores)
    winners = [i for i, s in enumerate(scores) if s == best]
    return winners[0] if len(winners) == 1 else None


class FrozenJudge:
    def __init__(self, arm, source, device="cuda"):
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        self.arm, self.torch, self.device = arm, torch, torch.device(device)
        self.tokenizer = AutoTokenizer.from_pretrained(source, local_files_only=True)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            source, local_files_only=True, use_safetensors=True).to(self.device)
        self.model.requires_grad_(False)
        self.model.eval()
        self.parameters = sum(p.numel() for p in self.model.parameters())
        expected = MODEL["expected_parameters"] if arm == "nli" else 22713601
        labels = 3 if arm == "nli" else 1
        if self.parameters != expected or self.model.config.num_labels != labels:
            raise ValueError("frozen architecture/parameter drift")
        if arm == "nli" and self.model.config.id2label != {0:"contradiction",1:"entailment",2:"neutral"}:
            raise ValueError("NLI label order drift")
        self.forward_calls = 0
        self.last_attempt = None

    def score(self, ir):
        began = perf_counter_ns()
        text = pairs(ir, self.arm)
        encoded = self.tokenizer([p[0] for p in text], [p[1] for p in text],
            padding=True, truncation=False, return_tensors="pt")
        if encoded["input_ids"].shape[1] > 256:
            raise ValueError("no silent truncation: pair length cap exceeded")
        self.last_attempt = {"input_rows": len(text),
            "input_tokens": int(encoded["attention_mask"].sum()),
            "padded_tokens": int(encoded["input_ids"].numel()), "forward_calls": 0}
        encoded = {k:v.to(self.device) for k,v in encoded.items()}
        self.torch.cuda.synchronize(self.device)
        forward = perf_counter_ns()
        self.forward_calls += 1
        self.last_attempt["forward_calls"] = 1
        with self.torch.inference_mode():
            logits = self.model(**encoded).logits
        self.torch.cuda.synchronize(self.device)
        forward_ms = (perf_counter_ns() - forward)/1e6
        matrix = logits.detach().float().cpu().tolist()
        scores = scores_from_logits(matrix, self.arm)
        return {**self.last_attempt, "logits": matrix, "scores": scores,
                "pairs": text, "forward_ms": forward_ms,
                "complete_ms": (perf_counter_ns()-began)/1e6}
