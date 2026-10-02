"""Pinned Gemma 4 adapter for Runtime-0.1 repair.

Uses the model's native chat/tool template and response parser. No training.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import resource
from time import perf_counter_ns

from neumann1.general_runtime_v106 import MODEL_ID, MODEL_REVISION, milliseconds, sha


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


class FrozenHFRepairCore:
    def __init__(self):
        started = perf_counter_ns()
        import torch
        import transformers
        from huggingface_hub import snapshot_download
        from transformers import AutoProcessor, AutoModelForMultimodalLM, Gemma4Processor

        self.torch, self.transformers = torch, transformers
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        torch.manual_seed(1061)

        self.path = Path(snapshot_download(MODEL_ID, revision=MODEL_REVISION, token=False))
        self.files = {
            str(p.relative_to(self.path)): file_hash(p)
            for p in sorted(self.path.rglob("*"))
            if p.is_file() and p.suffix in (".json", ".safetensors", ".jinja")
        }
        if not any(name.endswith(".safetensors") for name in self.files):
            raise ValueError("no pinned weights")

        self.processor = AutoProcessor.from_pretrained(
            self.path, local_files_only=True, trust_remote_code=False
        )
        if not isinstance(self.processor, Gemma4Processor):
            raise ValueError("pinned Gemma4Processor required")

        self.model = AutoModelForMultimodalLM.from_pretrained(
            self.path,
            local_files_only=True,
            trust_remote_code=False,
            dtype=torch.bfloat16,
        )
        self.model.eval()
        for parameter in self.model.parameters():
            parameter.requires_grad_(False)
        self.versions = tuple(parameter._version for parameter in self.model.parameters())

        self.identity = {
            "model_id": MODEL_ID,
            "revision": MODEL_REVISION,
            "artifact_sha256": sha(self.files),
            "files": self.files,
            "weights_frozen": True,
            "precision": "bfloat16",
            "device": "cpu",
            "parameters": sum(p.numel() for p in self.model.parameters()),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "torchvision": __import__("torchvision").__version__,
            "effective_tokenizer_vocab_sha256": sha(self.processor.tokenizer.get_vocab()),
            "evidence_kind": "actual_frozen_model",
            "interface": "gemma4_native_tools_prefix_parse",
        }
        self.startup_ms = milliseconds(started)

    def inputs(self, messages, tools, thinking):
        kwargs = {
            "tokenize": True,
            "return_dict": True,
            "return_tensors": "pt",
            "add_generation_prompt": True,
            "enable_thinking": thinking,
        }
        if tools:
            kwargs["tools"] = tools
        return self.processor.apply_chat_template(messages, **kwargs)

    def count_tokens(self, messages, tools, thinking):
        return int(self.inputs(messages, tools, thinking)["input_ids"].shape[-1])

    def generate(self, messages, tools, max_tokens, thinking, deadline_ms):
        started = perf_counter_ns()

        class Deadline(self.transformers.StoppingCriteria):
            def __call__(self, input_ids, scores, **kwargs):
                return milliseconds(started) >= deadline_ms

        inputs = self.inputs(messages, tools, thinking)
        n = int(inputs["input_ids"].shape[-1])
        if n >= 4096:
            raise ValueError("no context room for generation")

        with self.torch.inference_mode():
            generated = self.model.generate(
                **inputs,
                do_sample=False,
                max_new_tokens=min(max_tokens, 4096 - n),
                stopping_criteria=self.transformers.StoppingCriteriaList([Deadline()]),
            )

        tokens = generated[0, n:].tolist()
        if tuple(parameter._version for parameter in self.model.parameters()) != self.versions:
            raise ValueError("parameter mutation")

        raw = self.processor.decode(tokens, skip_special_tokens=False)
        parsed = None
        parse_error = None
        try:
            parsed = self.processor.parse_response(raw, prefix=inputs["input_ids"][0])
        except Exception as exc:
            parse_error = type(exc).__name__ + ": " + str(exc)

        return {
            "raw": raw,
            "parsed": parsed,
            "parser_error": parse_error,
            "input_tokens": n,
            "output_tokens": len(tokens),
            "output_token_ids": tokens,
            "thinking_enabled": thinking,
            "generation_ms": milliseconds(started),
            "deadline_reached": milliseconds(started) >= deadline_ms,
            "peak_process_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "core_sha256": sha(self.identity),
        }

    def audit(self):
        after = {name: file_hash(self.path / name) for name in self.files}
        unchanged = (
            after == self.files
            and tuple(parameter._version for parameter in self.model.parameters()) == self.versions
        )
        return {
            "unchanged": unchanged,
            "after_sha256": sha(after),
            "peak_process_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        }
