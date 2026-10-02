"""Frozen Gemma 4 E2B accelerator adapter for Architecture Multiplier AM1."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import resource
import subprocess
from time import perf_counter_ns

from neumann1.general_multiplier_contract import (
    FROZEN_ARTIFACT_SHA256,
    FROZEN_MODEL_ID,
    FROZEN_MODEL_REVISION,
    FROZEN_TOKENIZER_SHA256,
    validate_environment,
)
from neumann1.general_runtime_v106 import milliseconds, sha

MIN_ACCELERATOR_MEMORY_BYTES = 14 * 1024**3


def _file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _driver_string(torch):
    try:
        text = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.strip().splitlines()[0]
        if text:
            return text
    except Exception:
        pass
    return "cuda-runtime-" + str(torch.version.cuda)


class FrozenAcceleratorCore:
    def __init__(self):
        started = perf_counter_ns()
        import torch
        import transformers
        from huggingface_hub import snapshot_download
        from transformers import AutoModelForMultimodalLM, AutoProcessor, Gemma4Processor

        if not torch.cuda.is_available() or torch.cuda.device_count() < 1:
            raise RuntimeError("CUDA accelerator required; CPU fallback forbidden")
        self.torch = torch
        self.transformers = transformers
        self.device = torch.device("cuda:0")
        props = torch.cuda.get_device_properties(0)
        if int(props.total_memory) < MIN_ACCELERATOR_MEMORY_BYTES:
            raise RuntimeError(
                "accelerator memory below operational minimum: %d < %d"
                % (int(props.total_memory), MIN_ACCELERATOR_MEMORY_BYTES)
            )

        torch.manual_seed(12601)
        torch.cuda.manual_seed_all(12601)

        self.path = Path(snapshot_download(
            FROZEN_MODEL_ID,
            revision=FROZEN_MODEL_REVISION,
            token=False,
        ))
        self.files = {
            str(path.relative_to(self.path)): _file_hash(path)
            for path in sorted(self.path.rglob("*"))
            if path.is_file() and path.suffix in (".json", ".safetensors", ".jinja")
        }
        artifact_sha = sha(self.files)
        if artifact_sha != FROZEN_ARTIFACT_SHA256:
            raise ValueError("frozen artifact hash mismatch")

        self.processor = AutoProcessor.from_pretrained(
            self.path,
            local_files_only=True,
            trust_remote_code=False,
        )
        if not isinstance(self.processor, Gemma4Processor):
            raise ValueError("pinned Gemma4Processor required")
        tokenizer_sha = sha(self.processor.tokenizer.get_vocab())
        if tokenizer_sha != FROZEN_TOKENIZER_SHA256:
            raise ValueError("frozen tokenizer hash mismatch")

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
        torch.cuda.synchronize(self.device)

        self.environment = validate_environment({
            "device_type": "cuda",
            "device_name": torch.cuda.get_device_name(0),
            "accelerator_memory_bytes": int(props.total_memory),
            "precision": "bfloat16",
            "model_id": FROZEN_MODEL_ID,
            "model_revision": FROZEN_MODEL_REVISION,
            "artifact_sha256": artifact_sha,
            "tokenizer_sha256": tokenizer_sha,
            "deterministic": True,
            "do_sample": False,
            "framework": "torch-" + str(torch.__version__) + "/transformers-" + str(transformers.__version__),
            "driver": _driver_string(torch),
        })

        self.identity = {
            **self.environment,
            "weights_frozen": True,
            "accelerator_class": True,
            "files": self.files,
            "parameters": sum(parameter.numel() for parameter in self.model.parameters()),
            "torchvision": __import__("torchvision").__version__,
            "evidence_kind": "actual_frozen_model",
            "interface": "am1_compact_json_no_native_schema",
        }
        self.startup_ms = milliseconds(started)

    def _inputs(self, messages, thinking):
        return self.processor.apply_chat_template(
            messages,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            add_generation_prompt=True,
            enable_thinking=thinking,
        )

    def count_tokens(self, messages, thinking):
        return int(self._inputs(messages, thinking)["input_ids"].shape[-1])

    def generate(self, messages, max_tokens, thinking, deadline_ms):
        torch = self.torch
        started = perf_counter_ns()

        class Deadline(self.transformers.StoppingCriteria):
            def __call__(self, input_ids, scores, **kwargs):
                return milliseconds(started) >= deadline_ms

        cpu_inputs = self._inputs(messages, thinking)
        n = int(cpu_inputs["input_ids"].shape[-1])
        if n >= 4096:
            raise ValueError("no context room for generation")
        inputs = {
            key: value.to(self.device) if hasattr(value, "to") else value
            for key, value in cpu_inputs.items()
        }

        torch.cuda.synchronize(self.device)
        torch.cuda.reset_peak_memory_stats(self.device)
        generation_started = perf_counter_ns()
        with torch.inference_mode():
            generated = self.model.generate(
                **inputs,
                do_sample=False,
                max_new_tokens=min(max_tokens, 4096 - n),
                stopping_criteria=self.transformers.StoppingCriteriaList([Deadline()]),
            )
        torch.cuda.synchronize(self.device)
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
            "thinking_enabled": bool(thinking),
            "generation_ms": generation_ms,
            "deadline_reached": milliseconds(started) >= deadline_ms,
            "peak_accelerator_memory_bytes": int(torch.cuda.max_memory_allocated(self.device)),
            "peak_accelerator_reserved_bytes": int(torch.cuda.max_memory_reserved(self.device)),
            "peak_process_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "core_sha256": sha(self.identity),
        }

    def audit(self):
        after = {name: _file_hash(self.path / name) for name in self.files}
        unchanged = (
            after == self.files
            and sha(after) == FROZEN_ARTIFACT_SHA256
            and tuple(parameter._version for parameter in self.model.parameters()) == self.versions
        )
        return {
            "unchanged": unchanged,
            "after_artifact_sha256": sha(after),
            "current_accelerator_allocated_bytes": int(self.torch.cuda.memory_allocated(self.device)),
            "max_accelerator_allocated_bytes": int(self.torch.cuda.max_memory_allocated(self.device)),
            "max_accelerator_reserved_bytes": int(self.torch.cuda.max_memory_reserved(self.device)),
            "peak_process_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        }
