"""Prefix-aware frozen Gemma core for the v0.0.106 Runtime-0.1 repair.

The model load, weights, tokenizer, precision and audit are inherited unchanged
from the original v0.0.106 core.  Only response parsing follows the current
Transformers contract by supplying the generation prefix explicitly.
"""
from __future__ import annotations

import resource
from time import perf_counter_ns

from experiments.general_hf_core_v106 import FrozenHFCore
from neumann1.general_runtime_v106 import milliseconds, sha


class FrozenHFCoreRepair(FrozenHFCore):
    def generate(self, messages, max_tokens, thinking, deadline_ms):
        started = perf_counter_ns()

        class Deadline(self.transformers.StoppingCriteria):
            def __call__(self, input_ids, scores, **kwargs):
                return milliseconds(started) >= deadline_ms

        inputs = self.inputs(messages, thinking)
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
        if tuple(p._version for p in self.model.parameters()) != self.versions:
            raise ValueError("parameter mutation")
        raw = self.processor.decode(tokens, skip_special_tokens=False)
        parsed, parse_error = None, None
        try:
            parsed = self.processor.parse_response(raw, prefix=inputs["input_ids"])
        except Exception as exc:
            parse_error = type(exc).__name__ + ": " + str(exc)
        action_text = parsed.get("content") if type(parsed) is dict else None
        return {
            "raw": raw,
            "action_text": action_text,
            "parser_error": parse_error,
            "parser_prefix_supplied": True,
            "input_tokens": n,
            "output_tokens": len(tokens),
            "output_token_ids": tokens,
            "thinking_enabled": thinking,
            "generation_ms": milliseconds(started),
            "deadline_reached": milliseconds(started) >= deadline_ms,
            "peak_process_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "core_sha256": sha(self.identity),
        }
