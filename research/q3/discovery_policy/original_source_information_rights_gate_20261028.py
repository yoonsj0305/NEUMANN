"""Fail-closed executable research contract: distinguish evidence from a target oracle.

The synthetic finite-DSL experiment had a callable target value oracle for
every 8-bit x. Original external SyGuS constraints DON'T provide that right.
Never fabricate the missing f(x), or turn a verifier counterexample into an
unobserved gold target label.
"""
from dataclasses import dataclass
from enum import Enum
import re

class EvidenceKind(str,Enum):
    FINITE_LABELED_EXAMPLES="FINITE_LABELED_EXAMPLES"
    UNIVERSAL_FORMULA="UNIVERSAL_FORMULA"
    INDUCTIVE_TRANSITION_SYSTEM="INDUCTIVE_TRANSITION_SYSTEM"
    UNKNOWN="UNKNOWN"

@dataclass(frozen=True)
class SourceInformationRights:
    evidence_kind: EvidenceKind
    supplied_example_count: int
    has_candidate_verifier: bool
    has_source_formula_counterexamples: bool
    can_request_arbitrary_intended_target_label: bool
    original_fingerprint: str

def audited_rights(kind:EvidenceKind,n_examples:int,source_sha256:str):
    """Requires a separate actual connector/tool authorizing target labels.

    There is no such tool in the original SyGuS text; never infer it from
    semantic grammar completeness, examples or solver availability.
    """
    if n_examples<0 or not re.fullmatch(r"[0-9a-f]{64}",source_sha256):
        raise ValueError("SOURCE_SHA_OR_EXAMPLE_COUNT_INVALID")
    return SourceInformationRights(
        evidence_kind=kind,
        supplied_example_count=n_examples,
        has_candidate_verifier=kind!=EvidenceKind.UNKNOWN,
        has_source_formula_counterexamples=kind in (
            EvidenceKind.UNIVERSAL_FORMULA,EvidenceKind.INDUCTIVE_TRANSITION_SYSTEM),
        can_request_arbitrary_intended_target_label=False,
        original_fingerprint=source_sha256)

def request_arbitrary_target_label(rights:SourceInformationRights,x,
                                   explicit_callable_oracle=None):
    """No available oracle => NEVER manufacture a label from a candidate.

    A caller may provide a genuinely existing authorized callable oracle;
    it must be explicitly passed. Source constraints alone don't supply one.
    """
    if explicit_callable_oracle is None:
        return {"status":"HOLD_MISSING_INTENDED_TARGET_ORACLE",
                "has_gold_label":False,
                "query_input":repr(x),
                "original_sha256":rights.original_fingerprint}
    if not callable(explicit_callable_oracle):
        raise TypeError("ORACLE_IS_NOT_CALLABLE")
    return {"status":"AUTHORIZED_GOLD_LABEL_RETURNED",
            "has_gold_label":True,
            "target_output":explicit_callable_oracle(x),
            "original_sha256":rights.original_fingerprint}

def counterexample_is_not_gold_label(rights:SourceInformationRights,
                                     assignment):
    if not rights.has_source_formula_counterexamples:
        return {"status":"HOLD_SOURCE_NO_GENERAL_COUNTEREXAMPLE"}
    return {"status":"FORMULA_VIOLATION_ASSIGNMENT_ONLY",
            "counterexample_assignment":assignment,
            "intended_target_output_known":False}

def choose_feedback_channel(rights:SourceInformationRights):
    """Decision contracts, not a claimed trained neural metacontroller."""
    if rights.evidence_kind==EvidenceKind.FINITE_LABELED_EXAMPLES:
        return "CHECK_PUBLISHED_EXAMPLES_ONLY"
    if rights.evidence_kind==EvidenceKind.UNIVERSAL_FORMULA:
        return "FORMAL_SOURCE_SPEC_COUNTEREXAMPLE_NO_GOLD_TARGET"
    if rights.evidence_kind==EvidenceKind.INDUCTIVE_TRANSITION_SYSTEM:
        return "CHECK_THREE_INDUCTIVE_VCS_OR_REACHABLE_UNSAFETY"
    return "HOLD_UNKNOWN_INFORMATION_RIGHTS"
