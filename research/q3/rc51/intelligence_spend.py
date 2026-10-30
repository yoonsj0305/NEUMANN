"""RC51 compact research admission gate; full locally reproduced study in RC51 ZIP.
NEURAL_RESEARCH_ONLY is NOT permission for deployment or global Q closure.
"""
from dataclasses import dataclass
from typing import Optional
from fractions import Fraction

@dataclass(frozen=True)
class Evidence:
    baseline_correct: Optional[bool] = None
    baseline_proof: bool = False
    bounded_baselines_checked: int = 0
    classical_budget_limit_proven: bool = False
    independent_verifier: bool = False
    same_rights_baseline: bool = False
    allowed_bounded_research_budget: bool = False

def neural_spend_gate(e: Evidence):
    if e.baseline_correct is True and e.baseline_proof:
        return {"state": "EXECUTE_CLASSICAL",
                "neural_forwards_authorized": 0,
                "global_questions_closed": []}
    needed = {
      "strong_classical_budget": e.classical_budget_limit_proven,
      "bounded_baselines": e.bounded_baselines_checked > 0,
      "same_rights": e.same_rights_baseline,
      "independent_verifier": e.independent_verifier,
      "research_budget": e.allowed_bounded_research_budget,
    }
    missing = [k for k,v in needed.items() if not v]
    if missing:
        return {"state": "HOLD_UNKNOWN", "neural_forwards_authorized": 0,
                "missing": missing, "global_questions_closed": []}
    return {"state": "NEURAL_RESEARCH_ONLY",
            "neural_forwards_authorized": "CAPPED_RESEARCH_NOT_DEPLOYMENT",
            "global_questions_closed": []}

def batch_cpu_break_even(discovery_ns, classic_total_ns, retained_total_ns, n):
    if any(type(x) is not int or x < 0 for x in
           (discovery_ns, classic_total_ns, retained_total_ns)) or type(n) is not int or n < 1:
        raise ValueError("positive integer batch and nonnegative CPU ns only")
    delta = Fraction(classic_total_ns-retained_total_ns, n)
    threshold = (discovery_ns // delta + 1) if delta>0 else None
    after = discovery_ns+retained_total_ns
    return {"direct_cpu_ns": classic_total_ns,
            "learning_and_reuse_cpu_ns": after,
            "conditional_future_break_even_n": threshold,
            "observed_cpu_subtotal_gain": classic_total_ns / after if after else None,
            "is_full_iso_capability_10x_pass": False}

@dataclass(frozen=True)
class Resource:
    task_set_sha256: Optional[str] = None
    tool_rights_sha256: Optional[str] = None
    scope: str = "COMPLETE"
    verified: bool = False
    cpu_ns: Optional[int] = None
    peak_ram_bytes: Optional[int] = None
    joules_micro: Optional[int] = None
    usd_micro: Optional[int] = None

def resource_dominance(a, b, axes=("cpu_ns","peak_ram_bytes","joules_micro","usd_micro")):
    if not a.verified or not b.verified:
        return "NOT_COMPARABLE_UNVERIFIED"
    if (not a.task_set_sha256 or a.task_set_sha256 != b.task_set_sha256 or
        not a.tool_rights_sha256 or a.tool_rights_sha256 != b.tool_rights_sha256 or
        a.scope != b.scope):
        return "NOT_COMPARABLE_TASK_RIGHTS_OR_SCOPE"
    for ax in axes:
        v,w=getattr(a,ax),getattr(b,ax)
        if v is None or w is None: return "UNKNOWN_RESOURCE_" + ax.upper()
        if type(v) is not int or type(w) is not int or min(v,w)<0: raise ValueError("resource")
    return "PARETO_DOMINATES" if (
        all(getattr(a,ax)<=getattr(b,ax) for ax in axes) and
        any(getattr(a,ax)<getattr(b,ax) for ax in axes)) else "NOT_DOMINANT"

def finite_source_nonidentifiability(keys, unseen):
    if unseen in keys: raise ValueError("witness is not unseen")
    f=lambda _:0
    g=lambda x: int(x==unseen)
    assert all(f(x)==g(x) for x in keys)
    assert f(unseen)!=g(unseen)
    return "PROVED_SCOPE_ARBITRARY_FUNCTIONS"
