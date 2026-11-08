from __future__ import annotations

from .types import Problem, SolveResult, CostLedger, display_kind, is_unknown_kind
from .family_registry import FamilyRegistry
from .plugin_isolation import PluginProcessError
from .structural_meta_invention import StructuralMetaInventor, CertifiedProgram
from .meta_utility_policy import MetaUtilityEvidence


class RegistryEngine:
    """Execute a solver-ready IR through the adapter registered for its family."""

    def __init__(
        self,
        structure_former: object,
        registry: FamilyRegistry,
        min_confidence: float = 0.8,
        *,
        meta_inventor: StructuralMetaInventor | None = None,
    ):
        self.structure_former = structure_former
        self.registry = registry
        self.min_confidence = min_confidence
        self.meta_inventor = meta_inventor if meta_inventor is not None else StructuralMetaInventor()

    def solve(self, problem: Problem) -> SolveResult:
        ledger = CostLedger()
        trace: list[str] = []

        rep = self.structure_former.form(problem, ledger)
        trace.append(
            f"representation={display_kind(rep.kind)} confidence={rep.confidence:.3f}"
        )

        if is_unknown_kind(rep.kind) or rep.confidence < self.min_confidence:
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

        try:
            adapter = self.registry.get(rep.kind)
        except PermissionError as exc:
            ledger.fallback_steps += 1
            return SolveResult(
                answer=None,
                representation=rep,
                solver_name="fallback_required",
                verified=False,
                verification_reason=f"Plugin authorization denied: {exc}",
                ledger=ledger,
                trace=trace + ["authorization_fail_closed"],
            )
        except (TypeError, ValueError) as exc:
            ledger.fallback_steps += 1
            return SolveResult(
                answer=None,
                representation=rep,
                solver_name="fallback_required",
                verified=False,
                verification_reason=f"Invalid representation kind: {exc}",
                ledger=ledger,
                trace=trace + ["invalid_kind_fail_closed"],
            )

        if adapter is None:
            ledger.fallback_steps += 1
            return SolveResult(
                answer=None,
                representation=rep,
                solver_name="fallback_required",
                verified=False,
                verification_reason=(
                    f"No registered family adapter for {display_kind(rep.kind)}"
                ),
                ledger=ledger,
                trace=trace + ["unregistered_family_fail_closed"],
            )

        if not adapter.solver.supports(rep):
            ledger.fallback_steps += 1
            return SolveResult(
                answer=None,
                representation=rep,
                solver_name="fallback_required",
                verified=False,
                verification_reason="Registered family solver rejected its representation",
                ledger=ledger,
                trace=trace + ["solver_contract_fail_closed"],
            )

        trace.append(f"family={adapter.family_id}")
        trace.append(f"kind_id={adapter.canonical_kind_id}")
        trace.append(f"solver={adapter.solver.name}")
        try:
            answer = adapter.solver.solve(rep, ledger)
            vr = adapter.answer_verifier.verify(problem, rep, answer, ledger)
        except PluginProcessError as exc:
            ledger.fallback_steps += 1
            return SolveResult(
                answer=None,
                representation=rep,
                solver_name="fallback_required",
                verified=False,
                verification_reason=f"Plugin process fail-closed: {exc}",
                ledger=ledger,
                trace=trace + ["plugin_process_fail_closed"],
            )
        trace.append(f"verified={vr.ok}")

        return SolveResult(
            answer=answer,
            representation=rep,
            solver_name=adapter.solver.name,
            verified=vr.ok,
            verification_reason=vr.reason,
            ledger=ledger,
            trace=trace,
        )

    def observe_program(self, evidence: CertifiedProgram, *, verify):
        """Promote source-verified programs to the mutable method inventory."""
        return self.meta_inventor.observe(evidence, verify=verify)

    def invent_program(self, family: str, arity: int, *, params=(), verify=None, promote=True):
        """Run learned constructors through the caller's ORIGINAL verifier."""
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

    def synthesize_binary_operator(self, source_observations, query_pairs):
        """Induce a new finite-algebra representation and executable operator.

        This is not a choice among pre-coded task operators. It is an
        associativity/identity-conditional synthesis from I/O observations.
        All unseen query outputs are excluded from source_observations.
        Missing or contradictory evidence fails closed.
        """
        from .monoid_operator_inventor import invent_operator
        operator = invent_operator(source_observations)
        predictions = tuple(operator.apply(a, b) for a, b in query_pairs)
        return {"operator": operator,
                "representation": operator.normal_forms,
                "predictions": predictions}

    def synthesize_binary_operator_active(self, universe, source_oracle, *,
                                          query_budget, seed=0,
                                          validation_queries=12,
                                          allow_full_table=False):
        """Actively propose algebraic equations, query evidence and compile IR.

        The oracle is explicitly a source-time observation capability.
        Predictions are conditional unless all pairs have been observed.
        Source budget exhaustion, contradictions and unknown structures
        fail closed; full-table degraded mode requires explicit opt-in.
        """
        from .active_law_inventor import invent_with_oracle
        return invent_with_oracle(
            universe, source_oracle, budget=query_budget, seed=seed,
            validation=validation_queries, allow_full_table=allow_full_table)

    def synthesize_numeric_function_active(self, source_oracle, *, arity,
                                           max_degree=3, query_budget=120,
                                           seed=0, validation_queries=8):
        """Discover exact rational basis, coefficients and executable function.

        This source-oracle method is a second, independent math superfamily:
        polynomial functions, not finite associative binary operations.
        Its extrapolation remains conditional on the discovered grammar.
        """
        from .active_numeric_inventor import invent_numeric_function
        return invent_numeric_function(
            source_oracle,arity=arity,max_degree=max_degree,
            budget=query_budget,seed=seed,validation=validation_queries)

    def synthesize_relational_operator_active(self, row_symbols, column_symbols,
                                             source_oracle, *,
                                             query_budget, seed=0,
                                             patience=6, validation_queries=24,
                                             max_rank=12,
                                             trusted_rank_upper_bound=None):
        """Infer a NEW compact relation and executable rule from source queries.

        Independent of polynomial and associative-monad discovery. Provisional
        unless all cells observed or a trusted external rank premise holds.
        The rank premise is NOT certified by source fit.
        """
        from .active_rank_inventor import invent_rank_operator
        return invent_rank_operator(
            row_symbols, column_symbols, source_oracle,
            query_budget=query_budget, seed=seed, patience=patience,
            validation=validation_queries, max_rank=max_rank,
            rank_upper_bound=trusted_rank_upper_bound)

    def learn_boolean_constructor(self, source_oracle, *,
                                  max_source_queries=28):
        """Grow a persistent invented-method inventory from source tasks.

        The Boolean fold expression is not in a predefined operator list.
        Source programs at arity 2/3 are analyzed to construct a new reusable
        transition program; arity 4 provides an independent source check.
        """
        from .boolean_meta_inventor import invent_boolean_fold
        method = invent_boolean_fold(
            source_oracle, max_source_queries=max_source_queries)
        if not hasattr(self, "_source_invented_boolean_methods"):
            self._source_invented_boolean_methods = {}
        key = method.fingerprint()
        novel = key not in self._source_invented_boolean_methods
        self._source_invented_boolean_methods[key] = method
        return {"method_id": key, "method": method, "new_constructor": novel,
                "source_query_count": method.source_observations}

    def execute_boolean_constructor(self, method_id, input_bits):
        """Reuse a previously source-constructed executable method without queries.

        The result is conditional on the unproven recurrence hypothesis;
        caller's independent target verifier retains final authority.
        """
        inventory = getattr(self, "_source_invented_boolean_methods", {})
        if method_id not in inventory:
            from .boolean_meta_inventor import InsufficientEvidence
            raise InsufficientEvidence("constructor not in learned inventory")
        return inventory[method_id].apply(input_bits)

    def learn_invention_grammar(self, source_task_id, demonstrations, *, max_cost=4):
        """Induce reusable program grammar from certified source I/O only.

        Invented productions persist on this engine instance and do not use
        target gold. No arbitrary code execution or privileged family routing.
        """
        from .induced_grammar import GrammarInventor
        if not hasattr(self, "_invented_grammar"):
            self._invented_grammar=GrammarInventor(max_cost=max_cost)
        return self._invented_grammar.invent_from_source(source_task_id,demonstrations)

    def synthesize_with_invented_grammar(self, demonstrations):
        """Search the learned program grammar; source learning is separate."""
        from .induced_grammar import GrammarInventor
        if not hasattr(self, "_invented_grammar"):
            self._invented_grammar=GrammarInventor()
        return self._invented_grammar.solve(demonstrations,learned=True)

    def invention_grammar_rules(self):
        """Expose generated productions, not only cached task solutions."""
        return tuple(getattr(self,"_invented_grammar",None).productions) \
            if hasattr(self,"_invented_grammar") else ()
