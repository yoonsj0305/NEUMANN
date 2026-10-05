"""P1.11 P0: semantic micro-executor.

Prospective architecture after P1.10 partial evidence showed that a 5.1B
generative next-token controller can be both expensive and semantically weak
for tiny residual relation-selection problems.

P1.11 changes category: deterministic code reduces the task to a target semantic
role and candidate role descriptions, then a frozen sentence-semantic encoder
scores all candidates in one batched forward. Large generative inference is not
part of this P0 path.

No P1.11 model score is executed at import time.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re

SCHEMA = "neumann.control-plane-p1.11.semantic-microexecutor.p0.v1"

MODEL = {
    "model_id": "sentence-transformers/all-MiniLM-L6-v2",
    "model_revision": "1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
    "parameters": 22713728,
    "architecture": "BertModel",
    "embedding_dim": 384,
    "pooling": "attention-mask mean pooling then L2 normalization",
    "training": False,
}


@dataclass(frozen=True)
class Criteria:
    minimum_top_cosine: float = 0.0
    minimum_margin_cosine: float = 0.05


def contract():
    return {
        "schema": SCHEMA,
        "stage": "P0_SYNTHETIC_CONTRACT_ONLY",
        "model": dict(MODEL),
        "semantic_ir": "TARGET_ROLE_PLUS_SOURCE_BOUND_CANDIDATE_ROLE_DESCRIPTIONS",
        "large_generative_model_on_primary_path": False,
        "forward_calls_per_ambiguous_item": 1,
        "all_candidates_batched_together": True,
        "score": "cosine(target_embedding,candidate_role_embedding)",
        "winner_rule": "UNIQUE_TOP_ABOVE_ABSOLUTE_AND_MARGIN_GATES",
        "criteria": asdict(Criteria()),
        "removed_before_neural_compute": [
            "numeric_literals",
            "domains",
            "csp_constraints",
            "candidate_assignment_atoms",
            "solver_witnesses",
            "full_query",
        ],
        "generation": False,
        "retry": False,
        "hidden_reference_access": False,
        "new_training": False,
        "p110_result_rescued": False,
        "p110_task_score_reuse": False,
        "future_actual_requires_new_registered_tasks": True,
        "actual_model_run": "NOT_RUN",
        "development_registration": "NOT_REGISTERED",
        "fresh_validation_registered": False,
        "p2_registration_admitted": False,
        "p2_admitted": False,
        "decision3_admitted": False,
        "global_questions_closed": [],
    }


def semantic_role_ir(instruction, eligible_entities):
    """Extract the irreducible role-matching problem from a registered grammar.

    Expected public semantic grammar:
      X is the <role>, Y is the <role>, ...
      Resolve 'It' to the <target role>, then return a complete assignment.

    This function intentionally never receives the CSP query, literals, domains,
    private references or expected answer.
    """
    if type(instruction) is not str or not instruction:
        raise ValueError("nonempty semantic instruction required")
    if (
        type(eligible_entities) is not list
        or not 2 <= len(eligible_entities) <= 4
        or eligible_entities != sorted(set(eligible_entities))
        or any(type(x) is not str or not re.fullmatch(r"[A-Z]", x) for x in eligible_entities)
    ):
        raise ValueError("2..4 sorted unique source entity surfaces required")

    target_match = re.search(
        r"Resolve 'It' to the (.+?), then return a complete assignment\.$",
        instruction,
    )
    if target_match is None:
        raise ValueError("registered target-role clause required")
    target = target_match.group(1).strip()
    if not target:
        raise ValueError("nonempty target role required")

    prefix = instruction[: target_match.start()].strip()
    pairs = re.findall(r"\b([A-Z]) is the ([^,.]+)", prefix)
    role_by_entity = {}
    for entity, role in pairs:
        role = role.strip()
        if entity in role_by_entity or not role:
            raise ValueError("unique nonempty source role required")
        role_by_entity[entity] = role

    if set(role_by_entity) != set(eligible_entities):
        raise ValueError("semantic instruction must define exactly the eligible entities")

    candidates = [
        {"entity": entity, "role": role_by_entity[entity]}
        for entity in eligible_entities
    ]
    return {
        "target_role": target,
        "candidates": candidates,
    }


def select_from_similarities(ir, similarities, criteria=Criteria()):
    """Fail-closed deterministic selector over already-computed cosine scores."""
    if type(ir) is not dict or set(ir) != {"target_role", "candidates"}:
        raise ValueError("exact semantic role IR required")
    candidates = ir["candidates"]
    if (
        type(similarities) is not list
        or len(similarities) != len(candidates)
        or any(type(x) not in (int, float) or not -1.000001 <= float(x) <= 1.000001 for x in similarities)
    ):
        raise ValueError("one finite cosine score per candidate required")

    ranked = sorted(
        range(len(candidates)),
        key=lambda i: (-float(similarities[i]), candidates[i]["entity"]),
    )
    best, second = ranked[0], ranked[1]
    top = float(similarities[best])
    margin = top - float(similarities[second])

    if top < criteria.minimum_top_cosine:
        raise ValueError("P1.11 top semantic similarity below floor")
    if margin <= criteria.minimum_margin_cosine:
        raise ValueError("P1.11 semantic similarity margin failure")

    return {
        "selected_entity": candidates[best]["entity"],
        "selected_candidate_position": best,
        "top_cosine": top,
        "margin_cosine": margin,
        "candidate_cosines": {
            candidates[i]["entity"]: float(similarities[i])
            for i in range(len(candidates))
        },
    }


class FrozenMiniLMSemanticEncoder:
    """Lazy frozen all-MiniLM-L6-v2 backend.

    Uses the model-card Transformers path: AutoModel -> attention-mask mean
    pooling -> L2 normalization. One encode() call performs one batched model
    forward over target + all candidate descriptions.
    """

    def __init__(self, device="cpu"):
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.torch = torch
        self.device = torch.device(device)
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL["model_id"],
            revision=MODEL["model_revision"],
        )
        self.model = AutoModel.from_pretrained(
            MODEL["model_id"],
            revision=MODEL["model_revision"],
        ).to(self.device)
        self.model.eval()
        if sum(p.numel() for p in self.model.parameters()) != MODEL["parameters"]:
            raise ValueError("P1.11 frozen model parameter-count drift")
        self.forward_calls = 0

    def _mean_pool(self, hidden, attention_mask):
        torch = self.torch
        mask = attention_mask.unsqueeze(-1).expand(hidden.size()).float()
        return torch.sum(hidden * mask, 1) / torch.clamp(mask.sum(1), min=1e-9)

    def score(self, ir):
        import torch.nn.functional as F

        texts = [ir["target_role"]] + [row["role"] for row in ir["candidates"]]
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="pt",
        )
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        with self.torch.no_grad():
            output = self.model(**encoded)
        self.forward_calls += 1
        embeddings = self._mean_pool(output[0], encoded["attention_mask"])
        embeddings = F.normalize(embeddings, p=2, dim=1)
        target = embeddings[0]
        candidate = embeddings[1:]
        similarities = (candidate @ target).detach().cpu().tolist()

        return {
            "similarities": similarities,
            "forward_calls": 1,
            "input_rows": len(texts),
            "input_tokens": int(encoded["attention_mask"].sum().item()),
            "padded_tokens": int(encoded["input_ids"].numel()),
            "device": str(self.device),
        }
