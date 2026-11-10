"""One common learned hypothesis -> method proposal interface.

The latent hypothesis is a *model-authored, revisable explanation*, not a
human-authored task-family DSL. A verified executable method is still needed
for the current SOURCE checker. This does not itself prove causal discovery.
"""
from __future__ import annotations

from hashlib import sha256
import json

from .open_program_inventor import UnsafeProposal, validate_code
from .q3_source_repair_learning import recertified_repair_prompt


def hypothesis_prompt(source_prompt):
    """Same prompt string at neural training and inference time."""
    return (source_prompt +
        "\nBefore choosing an implementation, infer a falsifiable internal "
        "explanation of the observations. You may introduce new latent "
        "variables, relations and coordinate systems. Do not select a "
        "predefined domain operator. Revise the explanation when the prior "
        "program is refuted. Output ONLY one JSON object with exactly "
        "these keys: 'hypothesis' (a nonempty string explaining the "
        "unobserved relation and its testable consequences), and 'program' "
        "(a complete Python def transform(x) implementation). "
        "The program is only the current executor interface, not the "
        "definition of intelligence.\n")


def parse_hypothesis_proposal(raw):
    if not isinstance(raw,str) or len(raw)>12000:
        raise UnsafeProposal("bounded JSON hypothesis proposal required")
    try:
        data=json.loads(raw.strip())
    except (ValueError,TypeError) as exc:
        raise UnsafeProposal("expected one hypothesis/program JSON object") from exc
    if (not isinstance(data,dict) or set(data)!={"hypothesis","program"}
        or not isinstance(data["hypothesis"],str)
        or not 10<=len(data["hypothesis"])<=3000):
        raise UnsafeProposal("missing bounded falsifiable hypothesis")
    code=validate_code(data["program"])
    return data["hypothesis"],code


def completion(hypothesis,program):
    if not isinstance(hypothesis,str) or not 10<=len(hypothesis)<=3000:
        raise ValueError("real hypothesis trace required")
    return json.dumps({"hypothesis":hypothesis,
                       "program":validate_code(program)},
                      sort_keys=True,ensure_ascii=True,separators=(",",":"))


class HypothesisConditionedPolicy:
    """Use ONE neural policy for hypothesis and executable method together.

    Invention feedback comes from the same independent SOURCE checker as
    the existing SingleDiscoveryCore; no per-family branch or operator.
    The hypothesis is preserved for auditing, not treated as proven true.
    """
    def __init__(self,base_policy):
        self.base_policy=base_policy
        self.hypothesis_attempts=[]

    def propose(self,source_prompt):
        raw=self.base_policy.propose(hypothesis_prompt(source_prompt))
        hypothesis,code=parse_hypothesis_proposal(raw)
        self.hypothesis_attempts.append({
            "hypothesis":hypothesis,
            "hypothesis_sha256":sha256(hypothesis.encode()).hexdigest(),
            "program_sha256":sha256(code.encode()).hexdigest(),
            "prompt_sha256":sha256(source_prompt.encode()).hexdigest(),
            "provenance":"MODEL_AUTHORED_NOT_VERIFIED_CONCEPT",
        })
        return code


def recertified_hypothesis_repair_row(row,runner):
    """Train a changed explanation only from a real refuted prior program.

    Both prior and corrected method are checked by the existing SOURCE
    verifier. This function does not manufacture a hypothesis from gold.
    The row must carry a *model-authored* corrected explanation.
    """
    if row.get("hypothesis_provenance")!="MODEL_AUTHORED":
        raise ValueError("cannot teach invented explanation from a human label")
    hypothesis=row.get("corrected_hypothesis")
    if (not isinstance(hypothesis,str) or
        sha256(hypothesis.encode()).hexdigest()!=row.get("corrected_hypothesis_sha256")):
        raise ValueError("missing or tampered model-authored explanation")
    prompt,phase=recertified_repair_prompt(row,runner)
    return (hypothesis_prompt(prompt),
            completion(hypothesis,row["program"]),phase)
