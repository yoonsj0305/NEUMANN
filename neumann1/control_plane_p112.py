"""P1.12 P0: joint cross-encoder semantic judge.

Prospective architecture after P1.11.1 showed that independent sentence
embeddings plus cosine similarity are cheap but semantically insufficient.

P1.12 preserves the deterministic front end and one-batch micro-executor regime,
but changes the learned primitive to joint target-candidate scoring with a frozen
cross-encoder. No model is loaded and no model score is produced at import time.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter_ns

from neumann1.control_plane_p111 import semantic_role_ir

SCHEMA = "neumann.control-plane-p1.12.cross-encoder.p0.v1"

MODEL = {
    "model_id": "cross-encoder/ms-marco-MiniLM-L6-v2",
    "model_revision": "ce0834f22110de6d9222af7a7a03628121708969",
    "architecture": "BertForSequenceClassification",
    "expected_parameters": 22713601,
    "parameter_count_semantics": "sum(p.numel() for p in AutoModelForSequenceClassification.parameters())",
    "hidden_size": 384,
    "layers": 6,
    "labels": 1,
    "training": False,
}


@dataclass(frozen=True)
class PairTemplate:
    query_prefix: str = "Target function: "
    candidate_prefix: str = "Candidate role: "


def contract():
    return {
        "schema": SCHEMA,
        "stage": "P0_SYNTHETIC_CONTRACT_ONLY",
        "model": dict(MODEL),
        "semantic_ir": "JOINT_TARGET_CANDIDATE_ROLE_PAIRS",
        "large_generative_model_on_primary_path": False,
        "bi_encoder_cosine_on_primary_path": False,
        "cross_encoder_joint_interaction": True,
        "all_candidate_pairs_batched_together": True,
        "forward_calls_per_ambiguous_item": 1,
        "score": "single scalar relevance logit per target-candidate pair",
        "ranking_rule": "UNIQUE_TOP_LOGIT",
        "confidence_threshold": None,
        "confidence_calibration_deferred": True,
        "pair_template": asdict(PairTemplate()),
        "generation": False,
        "retry": False,
        "hidden_reference_access": False,
        "new_training": False,
        "p111_task_score_reuse": False,
        "p111_tasks_as_p112_evidence": False,
        "future_actual_requires_new_registered_tasks": True,
        "actual_model_run": "NOT_RUN",
        "development_registration": "NOT_REGISTERED",
        "fresh_validation_registered": False,
        "p2_registration_admitted": False,
        "p2_admitted": False,
        "decision3_admitted": False,
        "global_questions_closed": [],
    }


def build_joint_pairs(instruction, eligible_entities, template=PairTemplate()):
    """Build one target-candidate pair per eligible source-bound entity.

    The CSP query, numeric literals, domains, constraints, candidate assignment
    atoms, witnesses, expected label, and private references are never accepted
    by this function.
    """
    role_ir = semantic_role_ir(instruction, eligible_entities)
    target = role_ir["target_role"]
    pairs = []
    for candidate in role_ir["candidates"]:
        pairs.append({
            "entity": candidate["entity"],
            "query": template.query_prefix + target,
            "candidate_text": template.candidate_prefix + candidate["role"],
        })
    return {
        "target_role": target,
        "pairs": pairs,
    }



def _validate_joint_ir(ir):
    if type(ir) is not dict or set(ir) != {"target_role", "pairs"}:
        raise ValueError("exact P1.12 joint-pair IR required")
    target=ir["target_role"]
    pairs=ir["pairs"]
    if type(target) is not str or not target.strip():
        raise ValueError("nonempty target semantic role required")
    if type(pairs) is not list or not 2 <= len(pairs) <= 4:
        raise ValueError("2..4 semantic pair candidates required")
    entities=[]
    for row in pairs:
        if type(row) is not dict or set(row)!={"entity","query","candidate_text"}:
            raise ValueError("exact P1.12 candidate pair fields required")
        e=row["entity"]
        if type(e) is not str or len(e)!=1 or not ("A" <= e <= "Z"):
            raise ValueError("source-bound single uppercase entity required")
        if row["query"] != PairTemplate().query_prefix + target:
            raise ValueError("target pair query drift")
        role=row["candidate_text"]
        if type(role) is not str or not role.startswith(PairTemplate().candidate_prefix) or not role[len(PairTemplate().candidate_prefix):].strip():
            raise ValueError("nonempty source-bound candidate role required")
        entities.append(e)
    if entities != sorted(set(entities)):
        raise ValueError("distinct ordered candidate entities required")


def select_unique_top(ir, logits):
    """Select raw ranking winner only; confidence calibration is intentionally absent."""
    if type(ir) is not dict or set(ir) != {"target_role", "pairs"}:
        raise ValueError("exact P1.12 joint-pair IR required")
    _validate_joint_ir(ir)
    pairs = ir["pairs"]
    if (
        type(pairs) is not list
        or len(pairs) < 2
        or type(logits) is not list
        or len(logits) != len(pairs)
        or any(type(x) not in (int, float) for x in logits)
    ):
        raise ValueError("one finite scalar logit per candidate pair required")
    scores = [float(x) for x in logits]
    if any(x != x or x in (float("inf"), float("-inf")) for x in scores):
        raise ValueError("finite scalar logits required")

    ranked = sorted(
        range(len(pairs)),
        key=lambda i: (-scores[i], pairs[i]["entity"]),
    )
    best, second = ranked[0], ranked[1]
    if scores[best] == scores[second]:
        raise ValueError("P1.12 exact top-score tie")

    return {
        "selected_entity": pairs[best]["entity"],
        "selected_candidate_position": best,
        "top_logit": scores[best],
        "second_logit": scores[second],
        "raw_margin_logit": scores[best] - scores[second],
        "candidate_logits": {
            pairs[i]["entity"]: scores[i] for i in range(len(pairs))
        },
    }


class FrozenMiniLMCrossEncoder:
    """Lazy exact-revision cross-encoder backend for future actual studies."""

    def __init__(self, device="cpu", model_source=None, local_files_only=False):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.torch = torch
        self.device = torch.device(device)
        source = model_source or MODEL["model_id"]
        kwargs = {"local_files_only": bool(local_files_only)}
        if model_source is None:
            kwargs["revision"] = MODEL["model_revision"]

        self.tokenizer = AutoTokenizer.from_pretrained(source, **kwargs)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            source, **kwargs
        ).to(self.device)
        self.model.requires_grad_(False)
        self.model.eval()

        params = sum(p.numel() for p in self.model.parameters())
        if params != MODEL["expected_parameters"]:
            raise ValueError("P1.12 frozen model parameter-count drift")
        if getattr(self.model.config, "num_labels", None) != 1:
            raise ValueError("P1.12 single-logit cross-encoder required")

        self.forward_calls = 0
        self.last_attempt = None

    def score(self, ir):
        _validate_joint_ir(ir)
        pairs = ir["pairs"]
        queries = [row["query"] for row in pairs]
        candidates = [row["candidate_text"] for row in pairs]

        began = perf_counter_ns()
        encoded = self.tokenizer(
            queries,
            candidates,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="pt",
        )
        tokenize_ms = (perf_counter_ns() - began) / 1e6
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        attempt = {
            "input_rows": len(pairs),
            "input_tokens": int(encoded["attention_mask"].sum().item()),
            "padded_tokens": int(encoded["input_ids"].numel()),
        }
        self.last_attempt = {**attempt, "tokenize_ms": tokenize_ms}

        if self.device.type == "cuda":
            self.torch.cuda.synchronize(self.device)
        forward_start = perf_counter_ns()
        self.forward_calls += 1  # attempted work charged, even on model failure
        self.last_attempt["forward_calls"] = 1
        with self.torch.no_grad():
            output = self.model(**encoded)
        if self.device.type == "cuda":
            self.torch.cuda.synchronize(self.device)
        forward_ms = (perf_counter_ns() - forward_start) / 1e6
        self.last_attempt["forward_ms"] = forward_ms

        logit_start = perf_counter_ns()
        logits = output.logits
        if logits.ndim != 2 or logits.shape != (len(pairs), 1):
            raise ValueError("P1.12 one scalar logit per pair required")

        scores = logits[:, 0].detach().float().cpu().tolist()
        logit_extract_ms = (perf_counter_ns() - logit_start) / 1e6
        return {
            "logits": scores,
            "forward_calls": 1,
            **attempt,
            "tokenize_ms": tokenize_ms,
            "forward_ms": forward_ms,
            "logit_extract_ms": logit_extract_ms,
            "complete_ms": (perf_counter_ns() - began) / 1e6,
            "device": str(self.device),
        }
