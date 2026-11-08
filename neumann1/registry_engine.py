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

        Trustworthy classical solutions are tried first and independently
        checked. Invented methods execute only after a classical gap or an
        independent source-only utility admission. Verified classical ASTs
        may still grow the offline method inventory.
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

    def learn_invention_grammar(self, source_task_id, demonstrations, *,
                               max_cost=4, verification_pairs=None):
        """Induce reusable program grammar from certified source I/O only.

        Invented productions persist on this engine instance and do not use
        target gold. No arbitrary code execution or privileged family routing.
        """
        from .induced_grammar import GrammarInventor
        if not hasattr(self, "_invented_grammar"):
            self._invented_grammar=GrammarInventor(max_cost=max_cost)
        return self._invented_grammar.invent_from_source(
            source_task_id,demonstrations,verification_pairs=verification_pairs)

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

    def learn_recursive_control(self, source_tasks, *, independent_source_checks,
                                max_candidates=128):
        """Generate executable fixed-point/control grammar from source I/O.

        A separate source verifier must support the rule. This API does NOT
        claim to infer arbitrary new instruction semantics or target output.
        """
        from .induced_fixpoint_grammar import RecursiveGrammarInventor
        if not hasattr(self, "_recursive_grammar"):
            self._recursive_grammar = RecursiveGrammarInventor(
                max_candidates=max_candidates)
        rule = self._recursive_grammar.invent(
            source_tasks, verification_tasks=independent_source_checks)
        if rule.verified_for_all_finite_graphs:
            from .induced_grammar import GrammarInventor
            from hashlib import sha256
            if not hasattr(self, "_invented_grammar"):
                self._invented_grammar = GrammarInventor()
            name = "invented:" + sha256(repr(rule.ast).encode()).hexdigest()[:16]
            if name not in self._invented_grammar.dynamic_primitives:
                self._invented_grammar.register_generated_primitive(name, rule)
            self._recursive_primitive_name = name
        return rule

    def revise_recursive_control(self, source_counterexample):
        """Falsify and re-invent control structure; fail closed during repair."""
        from .induced_fixpoint_grammar import InsufficientEvidence
        if not hasattr(self, "_recursive_grammar"):
            raise InsufficientEvidence("no learned recursive grammar")
        if hasattr(self, "_invented_grammar") and hasattr(
                self, "_recursive_primitive_name"):
            self._invented_grammar.dynamic_primitives.pop(
                self._recursive_primitive_name, None)
        revised = self._recursive_grammar.revise_with_source_counterexample(
            source_counterexample)
        rule = self._recursive_grammar.learned[0]
        if rule.verified_for_all_finite_graphs:
            from .induced_grammar import GrammarInventor
            from hashlib import sha256
            if not hasattr(self, "_invented_grammar"):
                self._invented_grammar = GrammarInventor()
            name = "invented:" + sha256(repr(rule.ast).encode()).hexdigest()[:16]
            self._invented_grammar.register_generated_primitive(name, rule)
            self._recursive_primitive_name = name
        return revised

    def execute_recursive_control(self, target_input, *, optimized=True):
        """Execute only the promoted rule; unknown structures fail closed."""
        from .induced_fixpoint_grammar import InsufficientEvidence
        if not hasattr(self, "_recursive_grammar"):
            raise InsufficientEvidence("no learned recursive grammar")
        rule = self._recursive_grammar.learned[0]
        if optimized and rule.verified_for_all_finite_graphs:
            # The discovered rule is provably equivalent to a known BFS.
            # Use the strong established algorithm, not the slower invented
            # delta interpreter. Conditional on task semantics as elsewhere.
            from .classical_kernels import classical_directed_reachability
            return classical_directed_reachability(target_input)
        return self._recursive_grammar.solve(target_input, optimized=optimized)

    def solve_known_classical(self, task, *, semantics):
        """Zero-invention path for a caller-certified classical obligation.

        A trusted semantic adapter supplies 'semantics'. No source pattern
        or few-shot example is mistaken for mathematical certification.
        """
        from .classical_kernels import solve_with_semantic_contract
        return solve_with_semantic_contract(task, semantics=semantics)

    def synthesize_composed_arc_grid(self, source_examples, target_inputs, *,
                                     max_geometries=12,
                                     max_relational_ms=120):
        """Classical geometry first; invent only missing relational semantics.

        If strong classical grammar already EXACTLY fits source, no new
        relation is synthesized. This is a bounded source-only language
        expansion, not a proof of unrelated-domain universal generalization.
        """
        from .composed_grid_inventor import ComposedGridInventor
        return ComposedGridInventor(
            max_geometries=max_geometries,
            max_relational_ms=max_relational_ms).solve(
                source_examples,target_inputs)

    def synthesize_composed_semantics(self, source_examples,
                                      independent_source_checks, *,
                                      classical_candidates,
                                      pre_candidates, learn_residual,
                                      max_pre_candidates=16):
        """Single typed composition-discovery interface across data domains.

        Classical solutions are verified first. Unsupported residual tasks
        abstain; no target answers, family labels or hidden gold are used.
        Domain-specific primitive and residual plugins are caller-supplied,
        so this is not proof of universally self-invented semantics.
        """
        from .composition_meta_inventor import CompositionInventor
        return CompositionInventor(
            max_pre_candidates=max_pre_candidates).discover(
                source_examples,independent_source_checks,
                classical_candidates=classical_candidates,
                pre_candidates=pre_candidates,
                learn_residual=learn_residual)

    def invent_arc_object_only_on_classical_gap(
            self, source_examples, independent_source_checks, target_inputs,
            *, max_relational_ms=120, max_object_ms=350):
        """Use classical/previous original verifier FIRST, invent only on gap.

        Original target outputs are not accepted. Object grammar is learned
        from SOURCE observations and independently verified source checks.
        """
        from .object_gap_router import ObjectGapRouter
        response=ObjectGapRouter(
            max_relational_ms=max_relational_ms,
            max_object_ms=max_object_ms,
            known_causal_rules=getattr(self,"_q3_relation_memory",()),
            known_bulk_rules=getattr(self,"_q3_bulk_memory",())).solve(
                source_examples, independent_source_checks, target_inputs)
        # Method memory stores executable PROGRAM structure, never the
        # source/target answer table. Each later task re-verifies this
        # structure against that task's independent SOURCE examples.
        if response.origin=="SOURCE_VERIFIED_NEW_CAUSAL_RELATION":
            library=list(getattr(self,"_q3_relation_memory",()))
            for rule in response.invented_programs:
                if rule not in library:
                    library.append(rule)
            self._q3_relation_memory=tuple(library[-32:])
        if response.origin=="SOURCE_VERIFIED_NEW_BULK_RULE":
            library=list(getattr(self,"_q3_bulk_memory",()))
            for rule in response.invented_programs:
                if rule not in library:
                    library.append(rule)
            self._q3_bulk_memory=tuple(library[-32:])
        return response

    def invent_typed_relational_method(
            self, source_pairs, independent_source_checks, *,
            classical_solvers=(), max_source_ms=750):
        """Induce a typed program without a numeric/graph/spatial router.

        Classical specialist verified FIRST. Learned executable ASTs stored
        with a bounded library and independently SOURCE rechecked before
        reuse. This is bounded relational language, NOT universal Q3.
        """
        from .relational_meta_compiler import DomainIndependentRuleInventor
        evidence=DomainIndependentRuleInventor(
            max_ms=max_source_ms).invent(
                source_pairs,verification=independent_source_checks,
                classical_solvers=classical_solvers,
                known_programs=getattr(self,"_q3_typed_methods",()))
        if evidence.status=="SOURCE_VERIFIED_INVENTION":
            existing=list(getattr(self,"_q3_typed_methods",()))
            if evidence.program not in existing:
                existing.append(evidence.program)
            self._q3_typed_methods=tuple(existing[-32:])
        return evidence

    def invent_latent_representation(self, source_pairs,
                                     independent_source_checks, *,
                                     classical_solvers=(), max_degree=3,
                                     max_features=1000, max_source_ms=3000):
        """Create new symbolic interaction features from source-only raw facts.

        Classical solvers take priority; source/full-rank uniqueness and
        independent verification are required before any invented rule is
        executable. The language is bounded GF2 polynomials, not universal.
        """
        from .causal_representation_inventor import CausalRepresentationInventor
        return CausalRepresentationInventor(
            max_degree=max_degree,max_features=max_features,
            max_source_ms=max_source_ms).invent(
                source_pairs,
                independent_source_checks=independent_source_checks,
                classical_solvers=classical_solvers)

    def actively_invent_latent_representation(self, source_oracle, *,
                                               width,max_degree=3,
                                               independent_checks=64,
                                               seed=1007,
                                               classical_solvers=()):
        """Select source probes for latent features, never read target gold."""
        from .causal_representation_inventor import (
            invent_with_active_source_queries)
        return invent_with_active_source_queries(
            source_oracle,width=width,max_degree=max_degree,
            independent_checks=independent_checks,seed=seed,
            classical_solvers=classical_solvers)

    def discover_structural_orbit_representation(
            self, source_pairs, independent_source_checks, source_schema,
            *, classical_solvers=(), max_degree=4, max_source_ms=3000):
        """Invent latent source features, then discover a NEW orbit grammar.

        With an explicit coordinate-topology schema, source-induced
        interactions must form complete source symmetry orbits. If source
        evidence cannot certify the abstraction, return the source result
        without a structural program. Never read unseen target gold.
        """
        from .causal_representation_inventor import (
            CausalRepresentationInventor)
        from .symmetry_orbit_inventor import SymmetryOrbitInventor
        result=CausalRepresentationInventor(
            max_degree=max_degree,max_source_ms=max_source_ms).invent(
                source_pairs,
                independent_source_checks=independent_source_checks,
                classical_solvers=classical_solvers)
        if result.program is None:
            return result,None
        try:
            orbit=SymmetryOrbitInventor().invent(result.program,
                                                 source_schema)
        except (ValueError,TypeError):
            orbit=None
        return result,orbit

    def invent_hidden_graph_ontology(self, source_pairs,
                                      independent_source_checks,
                                      *, classical_solvers=(),
                                      max_degree=3,max_source_ms=3000):
        """Recover an otherwise unnamed graph ontology from source I/O.

        No graph schema or edges are supplied to the inventor. The method
        may abstain if source interactions do not identify unique star
        cliques and a complete learned structural motif.
        """
        from .causal_representation_inventor import (
            CausalRepresentationInventor)
        from .latent_graph_ontology import LatentGraphOntologyInventor
        learned=CausalRepresentationInventor(
            max_degree=max_degree,max_source_ms=max_source_ms).invent(
                source_pairs,independent_source_checks=independent_source_checks,
                classical_solvers=classical_solvers)
        if learned.program is None:
            return learned,None
        try:
            recovered=LatentGraphOntologyInventor().invent(learned.program)
        except (TypeError,ValueError):
            recovered=None
        return learned,recovered
