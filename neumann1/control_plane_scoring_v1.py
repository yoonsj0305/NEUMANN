"""Teacher-forced conditional label likelihood, with no generate() call.

Torch is optional and imported only by the tensor backend. No weights are loaded
here. An existing frozen core may be attached after its artifact audit passes.
"""
from __future__ import annotations

import math
from time import perf_counter_ns

from neumann1.control_plane_v1 import EncodedChoice, ScoreFailure, ScorePlan, ScoreResult, finite, snapshot


def label_mean_logprob(logits, prompt_length, label_ids):
    """Small independent reference for shifted causal suffix scoring in tests."""
    if type(prompt_length) is not int or prompt_length < 1 or not label_ids:
        raise ValueError("nonempty causal prefix and label required")
    values = []
    for offset, token in enumerate(label_ids):
        row = logits[prompt_length - 1 + offset]
        if type(token) is not int or not 0 <= token < len(row):
            raise ValueError("target outside vocabulary")
        maximum = max(finite(v) for v in row)
        norm = maximum + math.log(math.fsum(math.exp(v - maximum) for v in row))
        values.append(row[token] - norm)
    return math.fsum(values) / len(values)


class ChoiceScorer:
    """Tokenizer/forward separation permits exact admission before inference.

    Prefix and label token IDs are encoded separately, then concatenated. This
    explicit boundary is part of the scoring contract, not an unnoticed BPE
    substring boundary. Labels have no BOS/EOS; prefixes use the frozen template.
    """
    def __init__(self, encode_prefix, encode_label, backend, identity):
        self.encode_prefix = encode_prefix
        self.encode_label = encode_label
        self.backend = backend
        self.identity = snapshot(identity)

    def prepare(self, prompts, labels):
        rows = []
        for prompt in prompts:
            prefix = tuple(self.encode_prefix(prompt))
            for label in labels:
                rows.append(EncodedChoice(prefix, tuple(self.encode_label(label))))
        plan = ScorePlan(tuple(rows), len(prompts), tuple(labels))
        plan.validate()
        return plan

    def forward_bound(self, plan):
        return self.backend.forward_bound(plan)

    def evaluate(self, plan, remaining_ms):
        plan.validate()
        return self.backend.evaluate(plan, remaining_ms)


class TorchLabelBackend:
    def __init__(self, model, pad_token_id, device, batch_size=4):
        if type(batch_size) is not int or batch_size < 1:
            raise ValueError("positive batch size required")
        if type(pad_token_id) is not int or pad_token_id < 0:
            raise ValueError("pad token ID required")
        self.model = model
        self.pad_token_id = pad_token_id
        self.device = device
        self.batch_size = batch_size
        if model.training or any(p.requires_grad for p in model.parameters()):
            raise ValueError("eval mode and frozen parameters required")
        self.versions = tuple(p._version for p in model.parameters())

    def forward_bound(self, plan):
        return (len(plan.rows) + self.batch_size - 1) // self.batch_size

    def evaluate(self, plan, remaining_ms):
        import torch
        plan.validate()
        if finite(remaining_ms, True) <= 0:
            raise TimeoutError("no scoring time left")
        if self.model.training or any(p.requires_grad for p in self.model.parameters()):
            raise ValueError("model no longer frozen/eval")
        if tuple(p._version for p in self.model.parameters()) != self.versions:
            raise ValueError("parameter version drift")
        device = torch.device(self.device)

        def sync():
            if device.type == "cuda":
                torch.cuda.synchronize(device)

        sync()
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)
        began = perf_counter_ns()
        scores = []
        padded_tokens = calls = 0
        for first in range(0, len(plan.rows), self.batch_size):
            if (perf_counter_ns() - began) / 1e6 >= remaining_ms:
                raise ScoreFailure("scoring deadline; forward cannot be preempted", calls, padded_tokens,
                                   (perf_counter_ns() - began) / 1e6)
            chunk = plan.rows[first:first + self.batch_size]
            sequences = [r.prompt_ids + r.label_ids for r in chunk]
            width = max(map(len, sequences))
            padded_tokens += len(chunk) * width
            ids = torch.full((len(chunk), width), self.pad_token_id, dtype=torch.long, device=device)
            mask = torch.zeros_like(ids)
            # Request precisely the union of causal positions needed for labels.
            positions = sorted({len(r.prompt_ids) - 1 + i for r in chunk for i in range(len(r.label_ids))})
            keep = torch.tensor(positions, dtype=torch.long, device=device)
            index = {p: i for i, p in enumerate(positions)}
            for row, sequence in enumerate(sequences):
                ids[row, :len(sequence)] = torch.tensor(sequence, dtype=torch.long, device=device)
                mask[row, :len(sequence)] = 1
            with torch.inference_mode():
                calls += 1
                try:
                    output = self.model(input_ids=ids, attention_mask=mask, use_cache=False,
                                        logits_to_keep=keep, return_dict=True)
                except Exception as exc:
                    raise ScoreFailure(type(exc).__name__ + ": " + str(exc), calls, padded_tokens,
                                       (perf_counter_ns() - began) / 1e6) from exc
                if output.logits.shape[:2] != (len(chunk), len(positions)):
                    raise ValueError("selected causal-logit positions unsupported")
                logprobs = torch.log_softmax(output.logits.float(), dim=-1)
                for row, choice in enumerate(chunk):
                    target_positions = torch.tensor([index[len(choice.prompt_ids) - 1 + i]
                                                     for i in range(len(choice.label_ids))], device=device)
                    labels = torch.tensor(choice.label_ids, dtype=torch.long, device=device)
                    value = logprobs[row, target_positions, labels].mean().item()
                    scores.append(finite(value))
            sync()
            if (perf_counter_ns() - began) / 1e6 >= remaining_ms:
                raise ScoreFailure("scoring deadline; completed forward remains charged", calls, padded_tokens,
                                   (perf_counter_ns() - began) / 1e6)
        if tuple(p._version for p in self.model.parameters()) != self.versions:
            raise ValueError("parameter mutation")
        n = len(plan.labels)
        matrix = tuple(tuple(scores[i:i+n]) for i in range(0, len(scores), n))
        peak = int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else None
        return ScoreResult(matrix, calls, padded_tokens, peak)


def attach_frozen_gemma(core, batch_size=4):
    """Reuse the audited AM1 core; do not download, train or replace it."""
    from neumann1.general_multiplier_contract import (
        FROZEN_MODEL_ID, FROZEN_MODEL_REVISION, FROZEN_ARTIFACT_SHA256, FROZEN_TOKENIZER_SHA256,
    )
    expected = {"model_id": FROZEN_MODEL_ID, "model_revision": FROZEN_MODEL_REVISION,
                "artifact_sha256": FROZEN_ARTIFACT_SHA256, "tokenizer_sha256": FROZEN_TOKENIZER_SHA256,
                "precision": "bfloat16", "weights_frozen": True}
    if any(core.identity.get(k) != v for k, v in expected.items()) or not core.audit().get("unchanged"):
        raise ValueError("audited frozen Gemma identity required")
    processor = core.processor

    def prefix(prompt):
        result = processor.apply_chat_template(
            [{"role": "user", "content": prompt}], tokenize=True, return_dict=True,
            add_generation_prompt=True, enable_thinking=False)
        ids = result["input_ids"]
        if hasattr(ids, "tolist"):
            ids = ids.tolist()
        return ids[0] if ids and isinstance(ids[0], list) else ids

    tokenizer = processor.tokenizer
    backend = TorchLabelBackend(core.model, tokenizer.pad_token_id, core.device, batch_size)
    identity = {**snapshot(core.identity), "interface": "teacher_forced_fixed_labels_v1"}
    return ChoiceScorer(prefix, lambda text: tokenizer.encode(text, add_special_tokens=False), backend, identity)
