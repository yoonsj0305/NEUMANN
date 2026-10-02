"""Revision-pinned Gemma 4 E2B CUDA adapter for AM1.

This adapter is intentionally accelerator-only. It refuses CPU execution because
Decision 1 already stopped CPU runtime micro-tuning.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import resource
from time import perf_counter_ns

from neumann1.general_runtime_v106 import MODEL_ID, MODEL_REVISION, milliseconds, sha


MIN_TOTAL_VRAM_BYTES = 14 * 1024**3


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


class FrozenHFCudaCore:
    def __init__(self):
        started = perf_counter_ns()
        import torch
        import transformers
        from huggingface_hub import snapshot_download
        from transformers import AutoProcessor, AutoModelForMultimodalLM, Gemma4Processor

        if not torch.cuda.is_available() or torch.cuda.device_count() < 1:
            raise RuntimeError("CUDA accelerator required; CPU fallback forbidden by Decision 1")

        self.torch = torch
        self.transformers = transformers
        self.device = torch.device("cuda:0")
        props = torch.cuda.get_device_properties(0)
        if int(props.total_memory) < MIN_TOTAL_VRAM_BYTES:
            raise RuntimeError(
                "insufficient accelerator VRAM: %d < %d"
                % (int(props.total_memory), MIN_TOTAL_VRAM_BYTES)
            )

        torch.manual_seed(10701)
        torch.cuda.manual_seed_all(10701)

        self.path = Path(snapshot_download(MODEL_ID, revision=MODEL_REVISION, token=False))
        self.files = {
            str(path.relative_to(self.path)): file_hash(path)
            for path in sorted(self.path.rglob("*"))
            if path.is_file() and path.suffix in (".json", ".safetensors", ".jinja")
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
        self.model.to(self.device)
        self.model.eval()
        for parameter in self.model.parameters():
            parameter.requires_grad_(False)
        self.versions = tuple(parameter._version for parameter in self.model.parameters())

        torch.cuda.synchronize()
        self.identity = {
            "model_id": MODEL_ID,
            "revision": MODEL_REVISION,
            "artifact_sha256": sha(self.files),
            "files": self.files,
            "weights_frozen": True,
            "precision": "bfloat16",
            "device": "cuda:0",
            "accelerator_class": True,
            "accelerator_name": torch.cuda.get_device_name(0),
            "accelerator_capability": list(torch.cuda.get_device_capability(0)),
            "accelerator_total_memory_bytes": int(props.total_memory),
            "parameters": sum(parameter.numel() for parameter in self.model.parameters()),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "torchvision": __import__("torchvision").__version__,
            "effective_tokenizer_vocab_sha256": sha(self.processor.tokenizer.get_vocab()),
            "evidence_kind": "actual_frozen_model",
            "interface": "general_runtime_v106_custom_json_cuda",
        }
        self.startup_ms = milliseconds(started)

    def inputs(self, messages, thinking):
        return self.processor.apply_chat_template(
            messages,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            add_generation_prompt=True,
            enable_thinking=thinking,
        )

    def count_tokens(self, messages, thinking):
        return int(self.inputs(messages, thinking)["input_ids"].shape[-1])

    def generate(self, messages, max_tokens, thinking, deadline_ms):
        torch = self.torch
        started = perf_counter_ns()

        class Deadline(self.transformers.StoppingCriteria):
            def __call__(self, input_ids, scores, **kwargs):
                return milliseconds(started) >= deadline_ms

        inputs_cpu = self.inputs(messages, thinking)
        n = int(inputs_cpu["input_ids"].shape[-1])
        if n >= 4096:
            raise ValueError("no context room for generation")

        inputs = {
            key: value.to(self.device) if hasattr(value, "to") else value
            for key, value in inputs_cpu.items()
        }

        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats(self.device)
        generation_started = perf_counter_ns()
        with torch.inference_mode():
            generated = self.model.generate(
                **inputs,
                do_sample=False,
                max_new_tokens=min(max_tokens, 4096 - n),
                stopping_criteria=self.transformers.StoppingCriteriaList([Deadline()]),
            )
        torch.cuda.synchronize()
        generation_ms = milliseconds(generation_started)

        tokens = generated[0, n:].detach().cpu().tolist()
        if tuple(parameter._version for parameter in self.model.parameters()) != self.versions:
            raise ValueError("parameter mutation")

        raw = self.processor.decode(tokens, skip_special_tokens=False)
        return {
            "raw": raw,
            "input_tokens": n,
            "output_tokens": len(tokens),
            "output_token_ids": tokens,
            "thinking_enabled": thinking,
            "generation_ms": generation_ms,
            "deadline_reached": milliseconds(started) >= deadline_ms,
            "gpu_peak_allocated_bytes": int(torch.cuda.max_memory_allocated(self.device)),
            "gpu_peak_reserved_bytes": int(torch.cuda.max_memory_reserved(self.device)),
            "gpu_current_allocated_bytes": int(torch.cuda.memory_allocated(self.device)),
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
            "gpu_current_allocated_bytes": int(self.torch.cuda.memory_allocated(self.device)),
            "gpu_max_allocated_bytes": int(self.torch.cuda.max_memory_allocated(self.device)),
            "gpu_max_reserved_bytes": int(self.torch.cuda.max_memory_reserved(self.device)),
            "peak_process_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        }
