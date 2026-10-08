"""Small opened-development contract over existing certified executors.

No learned proposer, training admission, economic verdict or new proof system.
Domain payloads retain their original schemas. Certificates are produced again
by the existing executor constructors, never accepted from caller metadata.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from math import isfinite
from time import perf_counter

from neumann1.structural_data_rights import DataUseError, authorize


SCOPES = {
    "exact_integer_recurrence":
        "all integer parameters and nonnegative horizons; ordered original outputs",
    "exact_integer_recurrence_guarded":
        "original ordered goal from the bound initial state; all integer parameters and nonnegative integer horizons",
    "integer_list_right_fold":
        "all finite mathematical integer lists; ordered original fold outputs",
}
STAGES = ("investment", "startup", "structure", "discovery", "verify_compile",
          "execute_restore", "control", "failed_candidates", "fallback",
          "storage_transport")
ADDITIVE_AXES = ("wall_seconds", "cpu_resource_seconds", "gpu_resource_seconds",
                 "flops", "energy_joules", "money_usd")


def snapshot(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return sha256(snapshot(value).encode()).hexdigest()


@dataclass(frozen=True)
class StructuralState:
    variables: tuple[str, ...]
    relations: tuple[str, ...]
    constraints: tuple[str, ...]
    goal_sha256: str
    uncertainty: tuple[str, ...] = ("learned structural perception not implemented",)


@dataclass(frozen=True)
class ProblemView:
    domain: str
    original_json: str
    lineage: str
    state: StructuralState
    role: str = "D"

    @classmethod
    def opened(cls, domain, original, *, lineage, asset):
        # The caller must obtain payload through the existing rights-aware loader.
        # This is an API boundary, not an OS sandbox or automatic provenance proof.
        authorize(asset, "development_problem")
        if not isinstance(lineage, str) or not lineage.strip() or domain not in SCOPES:
            raise DataUseError("opened lineage and supported domain required")
        if domain in {"exact_integer_recurrence", "exact_integer_recurrence_guarded"}:
            from neumann1.inductive_perspective import validate_problem
            validate_problem(original)
            state = StructuralState(tuple(original["parameters"] + original["state"]),
                                    ("initial", "transition", "goal"),
                                    ("exact integers", "nonnegative horizon"),
                                    digest(original["goal"]))
        else:
            from neumann1.recursive_summary import validate_problem
            width = validate_problem(original)
            state = StructuralState(tuple(["head"] + [f"r{i}" for i in range(width)]),
                                    ("empty", "step", "ordered concatenation"),
                                    ("finite mathematical integer lists",), digest(original))
        return cls(domain, snapshot(original), lineage, state)

    @property
    def sha256(self):
        return digest({"domain": self.domain, "original": json.loads(self.original_json)})


@dataclass(frozen=True)
class PerspectiveProposal:
    problem_sha256: str
    program_json: str
    removed_computation: tuple[str, ...]
    preservation_scope: str
    reuse_conditions: tuple[str, ...]
    origin: str

    @classmethod
    def for_problem(cls, view, program, *, removed_computation, reuse_conditions, origin):
        if not origin or not removed_computation or not reuse_conditions:
            raise ValueError("proposal origin, removed work and reuse conditions required")
        return cls(view.sha256, snapshot(program), tuple(removed_computation),
                   SCOPES[view.domain], tuple(reuse_conditions), origin)

    @property
    def sha256(self):
        return digest(json.loads(self.program_json))


@dataclass(frozen=True)
class ValidityCertificate:
    accepted: bool
    status: str
    problem_sha256: str
    proposal_sha256: str
    scope: str
    evidence_json: str


@dataclass(frozen=True)
class CostReceipt:
    measurements_json: str
    scope: str
    peak_memory_json: str = '{"peak_ram_bytes":null,"peak_vram_bytes":null}'

    @classmethod
    def observed(cls, *, wall_seconds=None, scope):
        rows = {axis: {stage: None for stage in STAGES} for axis in ADDITIVE_AXES}
        for stage, value in (wall_seconds or {}).items():
            if stage not in STAGES or type(value) not in (int, float) or not isfinite(value) or value < 0:
                raise ValueError("finite nonnegative measurement in a declared stage required")
            rows["wall_seconds"][stage] = value
        return cls(snapshot(rows), scope)

    def complete_total(self, axis):
        if axis not in ADDITIVE_AXES:
            raise ValueError("only same-unit additive resources can be summed; peak bytes cannot")
        row = json.loads(self.measurements_json)[axis]
        if set(row) != set(STAGES):
            raise ValueError("complete stage declaration required")
        if any(v is not None and (type(v) not in (int, float) or not isfinite(v) or v < 0)
               for v in row.values()):
            raise ValueError("finite nonnegative resource values required")
        return None if any(v is None for v in row.values()) else sum(row.values())


@dataclass(frozen=True)
class ExperienceRecord:
    lineage: str
    proposal: PerspectiveProposal
    certificate: ValidityCertificate
    costs: CostReceipt
    allowed_use: str = "opened_development_only"
    training_activated: bool = False
    fresh_eligible: bool = False


@dataclass(frozen=True)
class ExecutionDecision:
    action: str
    reason: str


class PreparedPerspective:
    """Own a single certified engine and immutable input snapshots.

    Public proof records are descriptive. Mutating/replacing one cannot turn a
    rejected proposal into an executor. This is not protection from arbitrary
    Python that bypasses the API. No answer cache is used.
    """
    def __init__(self, view, proposal):
        if view.role != "D" or view.domain not in SCOPES:
            raise DataUseError("opened public development only")
        if (proposal.problem_sha256 != view.sha256 or
                proposal.preservation_scope != SCOPES[view.domain]):
            raise ValueError("proposal must bind original problem, goal and semantic scope")
        self._view, self._proposal = view, proposal
        self._engine = None
        original, program = json.loads(view.original_json), json.loads(proposal.program_json)
        start = perf_counter()
        try:
            if view.domain == "exact_integer_recurrence":
                from neumann1.inductive_perspective import compile_acceleration
                engine = compile_acceleration(original, program)
            elif view.domain == "exact_integer_recurrence_guarded":
                from neumann1.guarded_perspective import compile_guarded_acceleration
                if not isinstance(program, dict) or set(program) != {"proposal", "witness"}:
                    raise ValueError("separate guarded proposal/witness envelope required")
                engine = compile_guarded_acceleration(original, program["proposal"], program["witness"])
            else:
                from neumann1.recursive_summary import CertifiedSummary
                engine = CertifiedSummary(original, program)
            evidence = engine.certificate
            self._engine = engine
            accepted, status = True, "CERTIFIED"
        except (ValueError, RuntimeError) as error:
            # Existing constructors intentionally block UNKNOWN and refutation.
            # Do not infer a mathematical counterexample from an exception.
            evidence = {"error": str(error), "authority": "NOT_VERIFIED"}
            accepted, status = False, "NOT_VERIFIED"
        elapsed = perf_counter() - start
        certificate = ValidityCertificate(accepted, status, view.sha256, proposal.sha256,
                                          SCOPES[view.domain], snapshot(evidence))
        costs = CostReceipt.observed(wall_seconds={"verify_compile": elapsed},
                                    scope="adapter preparation only; discovery and investment UNKNOWN")
        self.experience = ExperienceRecord(view.lineage, proposal, certificate, costs)
        self.decision = ExecutionDecision(
            "ENGINEERING_ONLY" if accepted else "FALLBACK",
            "valid representation; economic and learned-discovery gates unproved" if accepted
            else "unverified proposal blocked; caller must charge failure and fallback")

    def run(self, request):
        if self._engine is None:
            raise ValueError("unverified proposal cannot execute")
        start = perf_counter()
        if self._view.domain in {"exact_integer_recurrence", "exact_integer_recurrence_guarded"}:
            if not isinstance(request, dict) or set(request) != {"parameters", "steps"}:
                raise ValueError("original parameters/horizon request required")
            output = self._engine.run(request["parameters"], request["steps"])
        else:
            output = self._engine.run(request)
        prior = json.loads(self.experience.costs.measurements_json)["wall_seconds"]
        known = {k: v for k, v in prior.items() if v is not None}
        known["execute_restore"] = perf_counter() - start
        receipt = CostReceipt.observed(wall_seconds=known,
                                      scope="one engineering call plus preparation; no amortization or total-cost claim")
        return output, receipt
