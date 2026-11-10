from __future__ import annotations
from .types import Problem, Representation, IRKind, CostLedger


class ExplicitStructureFormer:
    """Research scaffold.

    v0.0.1 intentionally does NOT pretend to understand arbitrary natural language.
    It accepts a candidate IR supplied in problem.metadata['candidate_ir'] and turns
    the execution/runtime side of NEUMANN into a testable system. The learned or LLM
    Structure Former is a later research component.
    """

    def form(self, problem: Problem, ledger: CostLedger) -> Representation:
        ledger.representation_steps += 1
        ir = problem.metadata.get("candidate_ir")
        if not ir:
            return Representation(
                kind=IRKind.UNKNOWN,
                payload={},
                confidence=0.0,
                rationale="No candidate IR supplied; fail closed.",
            )
        kind = IRKind(ir["kind"])
        return Representation(
            kind=kind,
            payload=ir.get("payload", {}),
            confidence=float(ir.get("confidence", 1.0)),
            rationale=ir.get("rationale", "explicit research scaffold"),
        )


class ExperienceStructureFormer:
    """Replace a supplied candidate_ir with a *learned, changeable* world state.

    Source observations and legal interventions are explicit inputs, not
    hidden gold. The underlying policy invents latent variable names,
    relations and predictions; the frozen one-shot sealed check controls
    whether the new representation may enter the existing solver path.

    This former is opt-in, with no new per-domain solver or Python-only
    output assumption. Existing ExplicitStructureFormer stays a comparator.
    """

    def __init__(self,causal_core):
        from .causal_experience import CausalExperienceCore
        if not isinstance(causal_core,CausalExperienceCore):
            raise TypeError("shared CausalExperienceCore required")
        self.core=causal_core

    def form(self,problem: Problem,ledger: CostLedger) -> Representation:
        ledger.representation_steps+=1
        md=problem.metadata
        ident=md.get("source_identity")
        if not isinstance(ident,str) or not ident:
            return Representation(
                kind=IRKind.UNKNOWN,payload={},confidence=0.0,
                rationale="no authorized SOURCE identity; fail closed")
        if self.core.task_id!=ident:
            queries=md.get("source_queries")
            sealed=md.get("sealed_source_query_ids",())
            if not isinstance(queries,dict) or not sealed:
                return Representation(
                    kind=IRKind.UNKNOWN,payload={},confidence=0.0,
                    rationale="no registered train/sealed observation boundary")
            self.core.start(
                ident,{"problem":problem.raw_text,
                       "observations":md.get("observations",())},
                queries,sealed_queries=sealed,
                target_queries=md.get("unlabeled_target_query_ids",()))
        return self.core.representation()

    def observe_source(self,query_id,actual,*,evidence_id,verify_source,
                       revise_context=None):
        """Authorized SOURCE -> error signal -> same learned policy update."""
        updates=self.core.observe(
            query_id,actual,evidence_id=evidence_id,
            verify_source=verify_source)
        if revise_context is not None:
            self.core.revise(revise_context)
        return updates

    def predict_unlabeled_target(self,query_id):
        """Return a frozen prediction, never a TARGET gold or training label."""
        return self.core.predict_target(query_id)

    def certify_source(self,query_id,actual,*,evidence_id,verify_source):
        """One-shot independent SOURCE proof, no adaptive learning."""
        self.core.freeze()
        return self.core.certify_sealed_source(
            query_id,actual,evidence_id=evidence_id,
            verify_source=verify_source)
