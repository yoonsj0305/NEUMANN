"""P1.8 CPU-only plumbing/proof/cost tests, NEVER fresh model evaluation."""
from itertools import product
import unittest
from unittest.mock import patch

from neumann1.control_plane_v1 import digest, snapshot
from neumann1.control_plane_p17 import build_candidates, compile_references
from neumann1.control_plane_p18 import Budget, contract, prune_candidates, validate_selection, interpret_and_execute
from experiments.control_plane_p14_dev import _executor
from tests.test_control_plane_p17 import view, scoring, Selector


def query(names="X,Y", clauses="X equals 0, It equals 1"):
    return view("Choose "+names+" from {0,1,2}. "+clauses+". Return a complete assignment.",
                "Return a complete assignment.")


def satisfies(project, answer):
    # Independent complete check, not the pruner's partial consistency routine.
    domains, rules = project["domains"], project["constraints"]
    if type(answer) is not dict or set(answer) != set(domains): return False
    if any(type(answer[k]) is not int or answer[k] not in domains[k] for k in domains): return False
    for op, name, other in rules:
        a, b = answer[name], answer[other] if type(other) is str else other
        if not {"eq": a == b, "ne": a != b, "lt": a < b, "le": a <= b}[op]: return False
    return True


def union_checker(v, answer):
    b = build_candidates(v)
    return any(satisfies(compile_references(v, b, i)["public"], answer) for i in range(len(b["candidates"])))


class FeasibilityContracts(unittest.TestCase):
    def test_contract_not_admission(self):
        c = contract()
        for key in ("p17_result_rescued", "p2_registration_admitted", "p2_admitted", "decision3_admitted",
                    "feasibility_is_semantic_equivalence", "generation", "retry"):
            self.assertIs(c[key], False)
        self.assertEqual(c["actual_gemma_run"], "NOT_RUN")
        self.assertEqual(c["global_questions_closed"], [])

    def test_budgets_strict(self):
        for value in (0, -1, True, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError): Budget(feasibility_nodes=value)
        with self.assertRaises(ValueError): Budget(whole_item_wall_ms=1)

    def test_unique_arithmetic_preserved_no_pruning_or_model(self):
        with patch("neumann1.control_plane_p18.prune_candidates", side_effect=AssertionError("no probe")):
            r = interpret_and_execute(view("Start with 44, divide by 4, add 3, multiply by 2"), _executor,
                                      lambda v, a: a == "28", lambda: self.fail("no model load"))
        self.assertTrue(r["accepted"])
        self.assertEqual((r["model_calls"], r["feasibility_calls"], r["specialist_calls"]), (0, 0, 1))

    def test_unique_csp_preserved(self):
        v = query(clauses="X equals 0, Y equals 1")
        r = interpret_and_execute(v, _executor, union_checker, lambda: self.fail("no model load"))
        self.assertTrue(r["accepted"])
        self.assertEqual((r["feasibility_calls"], r["specialist_calls"], r["witness_cache_hits"]), (0, 1, 0))

    def test_reducible_ambiguity_zero_neural_and_no_duplicate_search(self):
        v = query()
        r = interpret_and_execute(v, lambda *a: self.fail("no duplicate search"), union_checker,
                                  lambda: self.fail("no neural"))
        self.assertTrue(r["accepted"])
        self.assertEqual(r["eligible_indexes"], [1])
        self.assertEqual(r["selected_candidate"], 1)
        self.assertEqual(r["selection"], "UNIQUE_PROVEN_FEASIBLE_ZERO_NEURAL")
        self.assertEqual((r["model_calls"], r["neural_forward_calls"], r["generated_calls"]), (0, 0, 0))
        self.assertEqual((r["feasibility_calls"], r["specialist_calls"], r["witness_cache_hits"]), (2, 0, 1))
        self.assertEqual((r["tool_calls"], r["verifier_calls"]), (1, 1))

    def test_all_unsat_stop_without_executor_verifier_or_model(self):
        v = query(clauses="X equals 0, Y equals 0, It equals 1")
        fail = lambda *a: self.fail("must stop")
        r = interpret_and_execute(v, fail, fail, fail)
        self.assertEqual(r["status"], "NO_FEASIBLE_CANDIDATE")
        self.assertEqual([x["status"] for x in r["pruning_receipt"]["candidates"]], ["UNSAT", "UNSAT"])
        self.assertEqual((r["model_calls"], r["tool_calls"], r["verifier_calls"]), (0, 0, 0))

    def test_multiple_feasible_not_arbitrarily_promoted_unique(self):
        v = query(clauses="X is less than Y, It equals 1")
        r = interpret_and_execute(v, _executor, union_checker)
        self.assertEqual(r["status"], "NEEDS_BOUNDED_SEMANTIC_SELECTION")
        self.assertEqual(r["eligible_indexes"], [0, 1])
        self.assertFalse(r["executed"])

    def test_multiple_feasible_calls_selector_once(self):
        v = query(clauses="X is less than Y, It equals 1")
        s = Selector(chosen=1)
        r = interpret_and_execute(v, lambda *a: self.fail("reuse witness"), union_checker, lambda: s)
        self.assertTrue(r["accepted"])
        self.assertEqual(len(s.calls), 1)
        self.assertEqual((r["model_calls"], r["neural_forward_calls"]), (1, 36))
        self.assertEqual(r["witness_cache_hits"], 1)

    def test_holey_mask_no_reindexing(self):
        v = query("A,B,C", "B equals 0, It equals 1")
        b = build_candidates(v)
        self.assertEqual(prune_candidates(v, b)["sat_indexes"], [0, 2])
        self.assertEqual(validate_selection(v, b, [0, 2], scoring(v, b, 2)), 2)
        r = interpret_and_execute(v, _executor, union_checker, lambda: Selector(chosen=2))
        self.assertTrue(r["accepted"])
        self.assertEqual(r["selected_candidate"], 2)

    def test_impossible_global_winner_is_masked_not_executed(self):
        v = query("A,B,C", "B equals 0, It equals 1")
        b = build_candidates(v)
        r = scoring(v, b, 1)
        # Overall slot1 is impossible. Slot2 wins among feasible slots0,2.
        from neumann1.control_plane_p12 import PERMUTATIONS
        for p in r["passes"]:
            for row, mapping in zip(p["matrix"], PERMUTATIONS): row[mapping[2]] = -3.0
        self.assertEqual(validate_selection(v, b, [0, 2], r), 2)

    def test_node_cap_unknown_not_unsat(self):
        v = query()
        r = interpret_and_execute(v, _executor, union_checker, lambda: self.fail("no selector"),
                                  Budget(feasibility_nodes=1))
        self.assertEqual(r["status"], "FEASIBILITY_UNKNOWN")
        self.assertEqual(r["feasibility_nodes"], 1)
        self.assertTrue(r["pruning_receipt"]["unknown_indexes"])
        self.assertEqual((r["tool_calls"], r["verifier_calls"]), (0, 0))

    def test_constraint_cap_shared_across_candidates(self):
        v = query()
        p = prune_candidates(v, build_candidates(v), Budget(feasibility_constraint_checks=1))
        self.assertEqual(p["constraint_checks"], 1)
        self.assertTrue(p["unknown_indexes"])

    def test_unknown_after_sat_does_not_admit_unique(self):
        v = query(clauses="Y equals 0, It equals 1")
        p = prune_candidates(v, build_candidates(v))
        first_nodes = p["candidates"][0]["nodes"]
        r = interpret_and_execute(v, _executor, union_checker, budget=Budget(feasibility_nodes=first_nodes))
        self.assertEqual(r["pruning_receipt"]["candidates"][0]["status"], "SAT")
        self.assertEqual(r["status"], "FEASIBILITY_UNKNOWN")
        self.assertEqual(r["model_calls"], 0)

    def test_wall_cap_unknown(self):
        v = query()
        with patch("neumann1.control_plane_p18._Meter.elapsed", return_value=2000.0):
            p = prune_candidates(v, build_candidates(v))
        self.assertEqual(p["unknown_indexes"], [0, 1])
        self.assertEqual(p["probe_calls"], 0)

    def test_solver_exception_unknown_and_partial_work_retained(self):
        def failure(project, meter):
            meter.tick("node")
            raise RuntimeError("solver infrastructure failure")
        with patch("neumann1.control_plane_p18._probe", side_effect=failure):
            r = interpret_and_execute(query(), _executor, union_checker)
        self.assertEqual(r["status"], "FEASIBILITY_UNKNOWN")
        self.assertEqual(r["feasibility_nodes"], 2)
        self.assertTrue(r["accounting_complete"])
        self.assertEqual(r["tool_calls"], 0)

    def test_cached_witness_still_rejected_by_original_checker(self):
        from neumann1.control_plane_p18 import prune_candidates as original_prune
        def forged(*args):
            p = original_prune(*args)
            p["candidates"][1]["witness"]["X"] = 99
            return p
        with patch("neumann1.control_plane_p18.prune_candidates", side_effect=forged):
            r = interpret_and_execute(query(), _executor, union_checker)
        self.assertFalse(r["accepted"])
        self.assertEqual(r["verifier_calls"], 1)

    def test_cached_project_identity_drift_stops_before_verification(self):
        from neumann1.control_plane_p18 import prune_candidates as original_prune
        def forged(*args):
            p = original_prune(*args)
            p["candidates"][1]["project_sha256"] = "wrong"
            return p
        with patch("neumann1.control_plane_p18.prune_candidates", side_effect=forged):
            r = interpret_and_execute(query(), _executor, union_checker)
        self.assertFalse(r["accepted"])
        self.assertEqual(r["verifier_calls"], 0)
        self.assertIn("witness/project drift", r["execution"]["error"])

    def test_feasible_score_tie_stops(self):
        v = query(clauses="It equals 1"); b = build_candidates(v); r = scoring(v, b)
        from neumann1.control_plane_p12 import PERMUTATIONS
        for p in r["passes"]:
            for row, mapping in zip(p["matrix"], PERMUTATIONS): row[mapping[1]] = -1.0
        with self.assertRaises(ValueError): validate_selection(v, b, [0, 1], r)

    def test_item_deadline_no_execution(self):
        with patch("neumann1.control_plane_p18.perf_counter_ns", side_effect=[0] + [2000000000]*10000):
            r = interpret_and_execute(query(), _executor, union_checker,
                                      budget=Budget(feasibility_wall_ms=1, whole_item_wall_ms=1))
        self.assertFalse(r["accepted"])
        self.assertEqual(r["tool_calls"], 0)

    def test_selector_context_cap(self):
        v = query(clauses="It equals 1"); b = build_candidates(v); r = scoring(v, b)
        for p in r["passes"]:
            p["prefixes"] = [[7]*4097 for _ in range(24)]
        with self.assertRaises(ValueError): validate_selection(v, b, [0, 1], r)

    def test_sound_statuses_against_exhaustive_independent_check(self):
        for clauses in ("X equals 0, It equals 1", "X equals 0, Y equals 0, It equals 1",
                        "X is less than Y, It equals 1", "X differs from Y, It equals 2",
                        "X is at most Y, It equals 0"):
            v = query(clauses=clauses); b = build_candidates(v); p = prune_candidates(v, b)
            for row in p["candidates"]:
                project = compile_references(v, b, row["index"])["public"]
                domains = project["domains"]; names = sorted(domains)
                exists = any(satisfies(project, dict(zip(names, values)))
                             for values in product(*(domains[k] for k in names)))
                self.assertEqual(row["status"], "SAT" if exists else "UNSAT")
                if exists: self.assertTrue(satisfies(project, row["witness"]))
                self.assertEqual(row["project_sha256"], digest(project))

    def test_candidate_source_mutation_rejected(self):
        v = query(); b = build_candidates(v); b["candidates"][0]["atoms"][-1][0] = "NE"
        with self.assertRaises(ValueError): prune_candidates(v, b)

    def test_unique_bundle_not_pruned(self):
        v = view("Start with 1, add 2")
        with self.assertRaises(ValueError): prune_candidates(v, build_candidates(v))

    def test_private_metadata_never_reaches_pruner(self):
        for key in ("answer", "family", "task_id", "expected_candidate"):
            r = interpret_and_execute({**query(), key: 1}, _executor, union_checker)
            self.assertEqual(r["status"], "FAILED")
            self.assertEqual(r["feasibility_calls"], 0)

    def test_original_verifier_remains_final_authority_no_retry(self):
        r = interpret_and_execute(query(), _executor, lambda v, a: False, lambda: self.fail("no retry"))
        self.assertFalse(r["accepted"])
        self.assertTrue(r["executed"])
        self.assertEqual((r["tool_calls"], r["verifier_calls"]), (1, 1))

    def test_nonboolean_original_verifier_rejects(self):
        r = interpret_and_execute(query(), _executor, lambda v, a: 1)
        self.assertFalse(r["accepted"])
        self.assertIn("bool", r["execution"]["error"])

    def test_factory_failure_does_not_zero_unknown_neural_cost(self):
        def fail(): raise RuntimeError("startup failure")
        r = interpret_and_execute(query(clauses="It equals 1"), _executor, union_checker, fail)
        self.assertFalse(r["accounting_complete"])
        self.assertIsNone(r["neural_forward_calls"])
        self.assertEqual(r["model_calls"], 1)
        self.assertGreater(r["feasibility_nodes"], 0)

    def test_partial_selector_cost_retained(self):
        def partial(r):
            r["status"] = "FAILED"; r["ledger"]["forward_calls"] = 7
        r = interpret_and_execute(query(clauses="It equals 1"), _executor, union_checker,
                                  lambda: Selector(partial))
        self.assertFalse(r["accepted"])
        self.assertFalse(r["accounting_complete"])
        self.assertEqual(r["neural_forward_calls"], 7)
        self.assertEqual(r["tool_calls"], 0)

    def test_score_contract_tampering_fail_closed(self):
        v = query(clauses="It equals 1"); b = build_candidates(v)
        changes = [lambda r: r.update(unchanged=False), lambda r: r.update(generated_calls=1),
                   lambda r: r["identity"].update(model_revision="wrong"), lambda r: r["prompt_sha256"].reverse(),
                   lambda r: r["ledger"].update(forward_calls=0), lambda r: r.update(complete_ms=120001),
                   lambda r: r["passes"][0].update(peak_accelerator_memory_bytes=0),
                   lambda r: r["passes"][1]["prefixes"][0].append(100)]
        for change in changes:
            r = scoring(v, b); change(r)
            with self.subTest(change=change), self.assertRaises(ValueError): validate_selection(v, b, [0, 1], r)

    def test_mask_contract_strict(self):
        v = query(clauses="It equals 1"); b = build_candidates(v)
        for mask in ([0], [0, 0], [1, 0], [0, 2], [False, 1], (0, 1)):
            with self.subTest(mask=mask), self.assertRaises(ValueError): validate_selection(v, b, mask, scoring(v, b))

    def test_nonfinite_scores_fail_closed(self):
        v = query(clauses="It equals 1"); b = build_candidates(v); r = scoring(v, b)
        r["passes"][0]["matrix"][0][0] = float("nan")
        with self.assertRaises(ValueError): validate_selection(v, b, [0, 1], r)

    def test_batch_order_drift_rejected(self):
        v = query(clauses="It equals 1"); b = build_candidates(v); r = scoring(v, b)
        r["passes"][1]["matrix"][0][0] += 0.1
        with self.assertRaises(ValueError): validate_selection(v, b, [0, 1], r)

    def test_original_view_not_compiled_view_to_checker(self):
        v = query(); seen = []
        def check(original, answer): seen.append(original); return union_checker(original, answer)
        r = interpret_and_execute(v, _executor, check)
        self.assertTrue(r["accepted"])
        self.assertEqual(seen, [v])

    def test_timing_and_work_accounting_on_all_terminal_paths(self):
        for clauses in ("X equals 0, It equals 1", "X equals 0, Y equals 0, It equals 1", "It equals 1"):
            r = interpret_and_execute(query(clauses=clauses), _executor, union_checker)
            for key, value in r.items():
                if key.endswith("_ms"): self.assertGreaterEqual(value, 0)
            p = r["pruning_receipt"]
            self.assertEqual(r["feasibility_nodes"], sum(row["nodes"] for row in p["candidates"]))
            self.assertEqual(r["feasibility_constraint_checks"], sum(row["constraint_checks"] for row in p["candidates"]))
            self.assertEqual(r["complete_ms"] >= r["feasibility_ms"], True)


if __name__ == "__main__": unittest.main()
