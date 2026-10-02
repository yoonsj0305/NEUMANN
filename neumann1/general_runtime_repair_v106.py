"""Runtime-0.1 protocol repair candidate for the opened v0.0.106 controls.

This module does not replace or edit General Runtime-0.  It is an explicit,
charged adapter around the frozen core so the first Boot2 evidence remains
authoritative.  The repair has exactly two interface responsibilities:

1. bound hidden reasoning to zero tokens and require an immediate action;
2. normalize only unambiguous structured objects that omitted the action key.

Raw model bytes and the processor's original parsed content are retained in the
receipt.  No answer is synthesized, solved, corrected, or verified here.
"""
from __future__ import annotations

import json

from neumann1.general_runtime_v106 import canonical


REPAIR_ID = "v106r1-action-framing-bounded-reasoning"
REPAIR_SUFFIX = (
    " Runtime-0.1 opened repair contract: hidden thinking is disabled by the "
    "runtime. Emit the requested JSON action immediately and do not narrate "
    "outside JSON. When the strategy asks you to reason without tools, any "
    "visible rationale must be in the same JSON object and at most 24 words. "
    "For tool/representation strategies, choose the action instead of explaining "
    "what action you might take."
)


def _strip_json_fence(text):
    value = text.strip()
    for token in ("<turn|>", "<eos>"):
        value = value.replace(token, "")
    value = value.strip()
    if value.startswith("```json") and value.endswith("```"):
        value = value[7:-3].strip()
    elif value.startswith("```") and value.endswith("```"):
        value = value[3:-3].strip()
    return value


def normalize_action_text(text):
    """Return (normalized_text, rewrite_kind) without inventing semantics.

    Only three shapes are repaired:
      {"answer": ...}            -> final
      {"tool": ..., "args": ...} -> call
      {"ir": ...}                -> represent

    Objects that already carry an action are untouched.  Plain text, malformed
    JSON and ambiguous objects are untouched and therefore remain rejectable by
    the frozen Runtime-0 parser.
    """
    if type(text) is not str:
        return text, None
    stripped = _strip_json_fence(text)
    try:
        value = json.loads(stripped)
        canonical(value)  # preserve Runtime-0's NaN/Infinity rejection
    except Exception:
        return text, None
    if type(value) is not dict or "action" in value:
        return text, None

    shapes = []
    if "answer" in value:
        shapes.append("final")
    if "tool" in value and "args" in value:
        shapes.append("call")
    if "ir" in value:
        shapes.append("represent")
    if len(shapes) != 1:
        return text, None

    repaired = dict(value)
    repaired["action"] = shapes[0]
    return canonical(repaired), "insert_action:" + shapes[0]


class Runtime01ProtocolAdapter:
    """Transparent core adapter with charged prompt bytes and raw preservation."""

    def __init__(self, core):
        self.core = core
        self.identity = core.identity
        self.startup_ms = getattr(core, "startup_ms", 0.0)

    @staticmethod
    def _frame(messages):
        framed = [dict(message) for message in messages]
        if not framed or framed[0].get("role") != "system":
            raise ValueError("system prompt required")
        framed[0]["content"] = str(framed[0].get("content", "")) + REPAIR_SUFFIX
        return framed

    def count_tokens(self, messages, thinking):
        # The repair's bounded-reasoning rule is part of the measured protocol.
        return self.core.count_tokens(self._frame(messages), False)

    def generate(self, messages, max_tokens, thinking, deadline_ms):
        framed = self._frame(messages)
        result = dict(self.core.generate(framed, max_tokens, False, deadline_ms))
        original = result.get("action_text")
        source = original if type(original) is str else result.get("raw")
        normalized, rewrite = normalize_action_text(source)
        result["runtime01_repair"] = {
            "id": REPAIR_ID,
            "requested_thinking": bool(thinking),
            "effective_thinking": False,
            "rewrite": rewrite,
        }
        result["original_action_text"] = original
        if rewrite is not None:
            result["action_text"] = normalized
        return result

    def audit(self):
        return self.core.audit()
