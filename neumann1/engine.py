from __future__ import annotations
from typing import Iterable
from .types import Problem, SolveResult, CostLedger, IRKind
from .interfaces import StructureFormer, Solver, Verifier
from .structural_meta_invention import StructuralMetaInventor, CertifiedProgram
from .meta_utility_policy import MetaUtilityEvidence


class NeumannEngine:
    def __init__(self, structure_former: StructureFormer, solvers: Iterable[Solver], verifier: Verifier, min_confidence: float = 0.8, *, meta_inventor: StructuralMetaInventor | None = None):
        self.structure_former = structure_former
        self.solvers = list(solvers)
        self.verifier = verifier
        self.min_confidence = min_confidence
        # Persist learned executable method-constructors across solve calls.
        self.meta_inventor = meta_inventor if meta_inventor is not None else StructuralMetaInventor()

    def solve(self, problem: Problem) -> SolveResult:
        ledger = CostLedger()
        trace = []
        rep = self.structure_former.form(problem, ledger)
        trace.append(f"representation={rep.kind.value} confidence={rep.confidence:.3f}")

        if rep.kind == IRKind.UNKNOWN or rep.confidence < self.min_confidence:
            ledger.fallback_steps += 1
            return SolveResult(
                answer=None,
                representation=rep,
                solver_name="fallback_required",
                verified=False,
                verification_reason="Representation unknown or below confidence threshold",
                ledger=ledger,
                trace=trace + ["fail_closed"],
            )

        solver = next((s for s in self.solvers if s.supports(rep)), None)
        if solver is None:
            ledger.fallback_steps += 1
            return SolveResult(
                answer=None,
                representation=rep,
                solver_name="fallback_required",
                verified=False,
                verification_reason="No compatible deterministic solver",
                ledger=ledger,
                trace=trace + ["no_solver_fail_closed"],
            )

        trace.append(f"solver={solver.name}")
        answer = solver.solve(rep, ledger)
        vr = self.verifier.verify(problem, rep, answer, ledger)
        trace.append(f"verified={vr.ok}")
        return SolveResult(
            answer=answer,
            representation=rep,
            solver_name=solver.name,
            verified=vr.ok,
            verification_reason=vr.reason,
            ledger=ledger,
            trace=trace,
        )

    def observe_program(self, evidence: CertifiedProgram, *, verify):
        """Improve the live discovery METHOD INVENTORY from original-certified code."""
        return self.meta_inventor.observe(evidence, verify=verify)

    def invent_program(self, family: str, arity: int, *, params=(), verify=None, promote=True):
        """Generate a program using learned methods; never bypass original checking.

        A verified solution can become new training evidence and automatically
        induce another constructor method, not just grow a program cache.
        """
        return self.meta_inventor.solve(
            family, arity, params=params, verify=verify, promote=promote)

    def synthesize_program(self, family: str, arity: int, *,
                           params=(), verify=None, classical=None):
        """Solve a program task AND improve NEUMANN's reusable method language.

        No human observe_program call is needed. Certified classical outputs
        are inducted automatically; learned programs are preferred and
        independently reverified on each target obligation.
        """
        return self.meta_inventor.solve_or_discover(
            family, arity, params=params, verify=verify, classical=classical)

    def admit_meta_method_utility(self, family: str, *, discovery_wall_seconds: float,
            discovery_candidate_checks: int, validation_tasks: int,
            validation_cold_candidate_checks: int,
            validation_learned_candidate_checks: int,
            validation_cold_solved: int, validation_learned_solved: int,
            intended_future_tasks: int):
        """Admit or DELETE method search from the real inference hot path.

        Costs are source-only, must be measured before opening any target.
        Returning CLASSICAL_FIRST means the method remains archived but is
        not queried in solve_or_discover for this family.
        """
        evidence=MetaUtilityEvidence(
            discovery_wall_seconds=discovery_wall_seconds,
            discovery_candidate_checks=discovery_candidate_checks,
            validation_tasks=validation_tasks,
            validation_cold_candidate_checks=validation_cold_candidate_checks,
            validation_learned_candidate_checks=validation_learned_candidate_checks,
            validation_cold_solved=validation_cold_solved,
            validation_learned_solved=validation_learned_solved,
            intended_future_tasks=intended_future_tasks)
        return self.meta_inventor.admit_meta_method_utility(family,evidence)

    def synthesize_relational_grid(self, source_examples, target_input):
        """Infer an executable relational spatial program from example I/O.

        No gold target output or preferred ARC task ID is accepted. This
        complements the existing verification-gated symbolic method learner.
        An independent original target verifier still determines correctness.
        """
        from .relational_grid_inventor import RelationalGridInventor
        miner = RelationalGridInventor()
        hypothesis = miner.solve(source_examples)
        return {"prediction": miner.apply(hypothesis,target_input),
                "method": hypothesis.method,
                "source_fit": hypothesis.source_fit,
                "search_ms": hypothesis.elapsed_ms}

    def synthesize_arc_grid(self, source_examples, target_inputs, *, max_attempts=2):
        """Invent, route and execute two complementary ARC grid methods.

        Both branches receive the same original training examples. Neither
        receives held-out gold; the two final candidates are frozen before
        any independent task-level verifier scores their exact outputs.
        """
        from .hybrid_arc_grid_inventor import HybridArcGridInventor
        router=HybridArcGridInventor(max_attempts=max_attempts)
        return router.solve(source_examples,target_inputs)

    def synthesize_arc_grid_cost_aware(self, category: str, source_examples,
                                       target_inputs, *, source_policy):
        """Run exactly ONE source-selected program-discovery strategy.

        No target outputs are accepted, and a source-calibrated policy is
        required. Unlisted families fail closed rather than guessing
        whether to use the relational or cold execution path.
        """
        from .source_learned_grid_router import SourceLearnedGridRouter
        return SourceLearnedGridRouter(source_policy).solve(
            category, source_examples, target_inputs)
