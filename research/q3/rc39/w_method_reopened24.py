"""RC40 same-rights, same-runner W-method vs exhaustive source-only RC39 replay.

All 24 tasks are REOPENED. Only the membership function reaches hidden data
before hypotheses are frozen. Exact product proof is a grading-only second path.
"""
import json
from hashlib import sha1
from pathlib import Path
from time import process_time_ns

from research.q3.rc39.active_mealy import ActiveMealyLearner, MealyProgram
from research.q3.rc39.membership_conformance import SourceMeter, compare_source_rights
from research.q3.rc39.w_method_conformance import WMethodConformance
from research.q3.rc39.independent_first_grader import hidden_family, independent_product_prove

ROOT = Path(__file__).resolve().parents[3]
FAMILIES = ("prefix_parity", "prefix_mod3", "presence",
            "random_3state", "random_4state", "random_5state")
SEEDS = (39, 40, 41, 42)


def git_blob(path):
    b = path.read_bytes()
    return sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()


def run():
    pre = json.loads((ROOT / "docs/experiments/q3_RC40_W_METHOD_REOPENED24_PREREG_2026_11_06.json").read_text())
    lock = json.loads((ROOT / "docs/experiments/q3_RC39_FIRST_LEARNER_SOURCE_LOCK.json").read_text())
    assert git_blob(ROOT / "research/q3/rc39/active_mealy.py") == lock["original_source_git_blob"]
    assert pre["fixed_learner_git_blob"] == lock["original_source_git_blob"]
    start = process_time_ns()
    rows = []
    for family in FAMILIES:
        for seed in SEEDS:
            hidden = hidden_family(family, seed)
            assert hidden.n <= 5
            # This interface only returns observed outputs; no graph, state count,
            # or full equivalence oracle is injected into learner or W tester.
            membership_backend = lambda word, ref=hidden: ref.run(word)
            meter = SourceMeter(membership_backend, "ABC", "01", query_cap=100000)
            conformance = WMethodConformance(meter, 5, verification_word_cap=100000)
            learner = ActiveMealyLearner("ABC", "01", max_states=8,
                      max_membership=100000, max_equivalence=200)
            t0 = process_time_ns()
            learned = learner.learn(meter.membership, conformance.seek_counterexample)
            w_cpu_ms = (process_time_ns() - t0) / 1e6
            # Freeze compiled machine before independent reference-graph proof.
            ast = learned.source
            model = MealyProgram.from_source(ast) if ast else None
            proof = independent_product_prove(hidden, model) if model else {"equivalent":False}
            certificate = (learned.status == "SCOPED_ALL_LENGTHS_PROVED"
                           and conformance.certified_state_bound == 5)
            false_cert = bool(certificate and not proof["equivalent"])
            # Negative control: corrupt an observable INITIAL output.
            wrong_rejected = False
            if model:
                mutated = json.loads(json.dumps(ast))
                q = mutated["initial"]
                prior = mutated["emissions"][q][0]
                mutated["emissions"][q][0] = "1" if prior == "0" else "0"
                changed = MealyProgram.from_source(mutated)
                # Source-only W check; negative must NEVER receive a certificate.
                reject_meter = SourceMeter(membership_backend, "ABC", "01", query_cap=100000)
                reject_checker = WMethodConformance(reject_meter, 5, 100000)
                try:
                    counterexample = reject_checker.seek_counterexample(changed)
                    wrong_rejected = counterexample is not None
                except Exception as exc:
                    # Fail-closed UNKNOWN is rejection, but do not hide unexpected bugs.
                    from research.q3.rc39.active_mealy import UnknownStateStructure
                    if not isinstance(exc, UnknownStateStructure):
                        raise
                    wrong_rejected = True
                assert not independent_product_prove(hidden, changed)["equivalent"]
            # Exact same classical learner / input rights / bound; old exhaustive
            # conformance is a *new replay*, not a replacement FIRST receipt.
            t1 = process_time_ns()
            baseline = compare_source_rights(
                ActiveMealyLearner("ABC", "01", max_states=8,
                     max_membership=100000, max_equivalence=200),
                membership_backend, upper_bound=5, source_cap=100000,
                conformance_cap=100000)
            base_cpu_ms = (process_time_ns() - t1) / 1e6
            baseline_model = (MealyProgram.from_source(baseline["model_source"])
                              if baseline["model_source"] else None)
            baseline_proof = (independent_product_prove(hidden, baseline_model)
                              if baseline_model else {"equivalent":False})
            rows.append({
                "family":family, "seed":seed, "known_reference_states_auditor_only":hidden.n,
                "w_status":learned.status, "w_ast":ast,
                "w_certificate":certificate, "w_independent_exact":proof["equivalent"],
                "w_false_certificate":false_cert, "negative_mutant_rejected":wrong_rejected,
                "w_unique_source_queries":meter.unique_queries,
                "w_unique_source_symbols":meter.unique_query_symbols,
                "w_conformance_words_checked":conformance.total_words_checked,
                "w_conformance_callbacks":conformance.callbacks,
                "w_cpu_ms":w_cpu_ms,
                "baseline_status":baseline["status"],
                "baseline_independent_exact":baseline_proof["equivalent"],
                "baseline_unique_source_queries":baseline["total_unique_source_membership_calls"],
                "baseline_unique_source_symbols":baseline["total_unique_source_symbols"],
                "baseline_conformance_words_checked":baseline["conformance_full_word_checks"],
                "baseline_cpu_ms":base_cpu_ms
            })
    def total(key):
        return sum(row[key] for row in rows)
    w_queries = total("w_unique_source_queries")
    base_queries = total("baseline_unique_source_queries")
    all_exact = (len(rows)==24 and all(row["w_certificate"] and row["w_independent_exact"]
                 and row["baseline_status"] == "SCOPED_ALL_LENGTHS_PROVED"
                 and row["baseline_independent_exact"] for row in rows))
    no_false = (not any(row["w_false_certificate"] for row in rows)
                and all(row["negative_mutant_rejected"] for row in rows))
    same_original_baseline = (base_queries == 172051
                 and total("baseline_unique_source_symbols") == 1362696
                 and total("baseline_conformance_words_checked") == 172499)
    strict_primary = all_exact and no_false and same_original_baseline and w_queries <= 17205
    return {
        "schema":"neumann.q3.rc40.w-method-same-rights-reopened24.v1",
        "science_status":"SCOPED_W_QUERY_10X_PASS" if strict_primary else "SCOPED_W_QUERY_10X_FAIL",
        "reopened_original_tasks":24,
        "source_interface":"membership_only_plus_trusted_reference_state_bound_5",
        "hidden_reference_graph_given_to_learner_or_conformance":False,
        "same_runner_baseline":"exhaustive_WORST_CASE_N_PLUS_M_MINUS_1",
        "source_learner_blob":lock["original_source_git_blob"],
        "original_20261106_first_receipt_replaced":False,
        "metrics":{
           "w_independent_all_length":sum(row["w_independent_exact"] for row in rows),
           "exhaustive_independent_all_length":sum(row["baseline_independent_exact"] for row in rows),
           "w_completed_certificates":sum(row["w_certificate"] for row in rows),
           "w_false_certificates":sum(row["w_false_certificate"] for row in rows),
           "wrong_mutants_rejected":sum(row["negative_mutant_rejected"] for row in rows),
           "w_unique_source_queries":w_queries,
           "baseline_unique_source_queries":base_queries,
           "w_unique_source_symbols":total("w_unique_source_symbols"),
           "baseline_unique_source_symbols":total("baseline_unique_source_symbols"),
           "w_conformance_words_checked":total("w_conformance_words_checked"),
           "baseline_conformance_words_checked":total("baseline_conformance_words_checked"),
           "same_rights_membership_query_reduction_factor":base_queries/w_queries if w_queries else None,
           "w_cpu_ms":total("w_cpu_ms"),
           "baseline_cpu_ms":total("baseline_cpu_ms"),
           "end_to_end_process_cpu_ms":(process_time_ns()-start)/1e6
        },
        "scientific_limits":{
            "global_Q3_learned_new_architecture":"OPEN",
            "Q4_equal_rights_end_to_end_10x":"OPEN",
            "Q6_external_semantic_family_transfer":"OPEN",
            "Q7_frontier_problem_solving":"OPEN",
            "source_state_upper_bound_required":True,
            "any_new_task_family_held_out":False
        },
        "rows":rows
    }


if __name__=="__main__":
    result=run()
    print(json.dumps(result,indent=2))
    if result["science_status"] != "SCOPED_W_QUERY_10X_PASS":
        raise SystemExit(1)
