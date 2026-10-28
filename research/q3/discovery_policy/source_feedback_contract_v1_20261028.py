"""NEUMANN G1 formal-source information-rights firewall.

Unknown program intent is never a callable output oracle merely because
examples, program synthesis constraints, or a counterexample verifier exist.
This explicitly prevents the finite self-authored 8-bit oracle simulator from
being silently used as an external SyGuS benchmark right.
"""
from dataclasses import dataclass
from enum import Enum
import re

class SourceKind(str, Enum):
    PBE_GROUND_EXAMPLES = "PBE_GROUND_EXAMPLES"
    FORMAL_SYNTHESIS = "FORMAL_SYNTHESIS"
    INDUCTIVE_INVARIANT = "INDUCTIVE_INVARIANT"
    MIXED_OR_UNPARSED = "MIXED_OR_UNPARSED"

class FeedbackKind(str, Enum):
    SOURCE_EXAMPLE = "SOURCE_EXAMPLE"
    CANDIDATE_COUNTEREXAMPLE = "CANDIDATE_COUNTEREXAMPLE"
    TRUE_TARGET_OUTPUT = "TRUE_TARGET_OUTPUT"

class MissingSourceRight(PermissionError):
    pass

@dataclass(frozen=True)
class FeedbackContract:
    source_kind: SourceKind
    original_constraints: int
    original_invariant_constraints: int
    original_ground_example_count: int
    has_true_target_output_oracle: bool
    may_request_formal_counterexample: bool
    may_verify_published_examples: bool
    original_full_truth_table_available: bool

    def authorize(self, request: FeedbackKind) -> bool:
        if request == FeedbackKind.TRUE_TARGET_OUTPUT:
            if not self.has_true_target_output_oracle:
                raise MissingSourceRight("No callable unseen-target output oracle exists in the published SyGuS source")
            return True
        if request == FeedbackKind.CANDIDATE_COUNTEREXAMPLE:
            if not self.may_request_formal_counterexample:
                raise MissingSourceRight("Source gives only finite examples, not a generic unknown-output counterexample oracle")
            return True
        if request == FeedbackKind.SOURCE_EXAMPLE:
            if not self.may_verify_published_examples:
                raise MissingSourceRight("No ground examples explicitly provided")
            return True
        raise ValueError("Unknown feedback request")

def audit_form_counts(form_pairs):
    """Parse the trusted top-level original-form (command, source) pairs.

    A synthesis constraint with a ground equation f(c)=d is a PROVIDED sample,
    not evidence that an oracle can answer arbitrary f(x) labels.
    """
    synth=[]
    ordinary=[]
    inv=0
    declare_vars=0
    for kind,source in form_pairs:
        if kind in ("synth-fun","synth-inv"):
            m=re.match(r"^\(\s*(?:synth-fun|synth-inv)\s+([^\s()]+)",source)
            if m:synth.append(m.group(1))
        if kind=="constraint":ordinary.append(source)
        if kind=="inv-constraint":inv+=1
        if kind=="declare-var":declare_vars+=1
    grounds=0
    for f in ordinary:
        if any(re.search(r"^\(\s*constraint\s+\(=\s+\(\s*"+re.escape(name)+r"(?:\s|\))",f)
               for name in synth):
            grounds+=1
    if inv:
        kind=SourceKind.INDUCTIVE_INVARIANT
    elif ordinary and len(ordinary)==grounds and declare_vars==0:
        kind=SourceKind.PBE_GROUND_EXAMPLES
    elif ordinary:
        kind=SourceKind.FORMAL_SYNTHESIS
    else:
        kind=SourceKind.MIXED_OR_UNPARSED
    return FeedbackContract(
        source_kind=kind,
        original_constraints=len(ordinary),
        original_invariant_constraints=inv,
        original_ground_example_count=grounds,
        has_true_target_output_oracle=False,
        may_request_formal_counterexample=(kind in
            (SourceKind.FORMAL_SYNTHESIS,SourceKind.INDUCTIVE_INVARIANT)),
        may_verify_published_examples=(grounds>0),
        original_full_truth_table_available=False)

def oracle_counterexample_is_a_true_label(candidate_result):
    """Conservative: formal violation ≠ the unknown intended output.

    If a constraint explicitly equates f(x) to known y, y is a PUBLISHED
    source example, never an on-demand label of an unseen input.
    """
    return False
