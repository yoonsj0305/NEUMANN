"""Task-agnostic Q3 latent hypothesis policy: hypothesis -> new full program.

The SAME trainable model learns to posit hidden causal variables and invariants
before writing Python. No human-specified target operator, AST edit rule,
named family router, image grammar, task-ID switch, or answer lookup.

The outer GenerativeProgramInventor remains unchanged and solely controls
SOURCE-only execution, sealed independent checks and abstention. This wrapper
returns model-authored code; the hypothesized natural-language cause is NOT
treated as scientific proof or as an executable solver.
"""
from __future__ import annotations

from .q3_prompt_contract import SourceContextOverflow


class LatentCausalHypothesisPolicy:
    """One latent-hypothesis forward pass plus one executable code proposal."""

    def __init__(self,base_model,*,max_hypothesis_chars=1800):
        if not 100<=max_hypothesis_chars<=4000:
            raise ValueError("finite causal hypothesis budget required")
        if not hasattr(base_model,"hypothesize") or not hasattr(
                base_model,"propose"):
            raise ValueError("one shared model must support both stages")
        self.base_model=base_model
        self.max_hypothesis_chars=max_hypothesis_chars
        self.attempts=0
        self.last_hypothesis=None

    def propose(self,source_only_prompt):
        if not isinstance(source_only_prompt,str) or not source_only_prompt:
            raise ValueError("real SOURCE observation required")
        raw=self.base_model.hypothesize(source_only_prompt)
        if not isinstance(raw,str) or not raw.strip():
            raise SourceContextOverflow(
                "no causal hypothesis produced; abstain, never invent metadata")
        hypothesis=raw.strip()[:self.max_hypothesis_chars]
        self.last_hypothesis=hypothesis
        self.attempts+=1
        # The model, not a fixed rule library, decides which latent relation
        # may explain observed changes; it then writes its own full algorithm.
        executable_prompt=(
            source_only_prompt+
            "\nModel-proposed, UNVERIFIED latent causal hypothesis "
            "(may be false):\n"+
            hypothesis+
            "\nWrite a self-contained executable Python "
            "def transform(x) that implements a general causal rule "
            "inferred from the SOURCE, NOT a list of memorized edits. "
            "Treat your hypothesis as fallible. Return only code.\n"
        )
        return self.base_model.propose(executable_prompt)
