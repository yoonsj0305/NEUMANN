"""Protect real historical inference, exposure boundaries and cost projections."""
import csv
import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from research.audit import analyze_retained_lp as audit
from research.audit import build_registry as registry
from research.audit import analyze_certificate_geometry as geometry
from research.audit import analyze_q34_mechanism as q34
from research.audit import analyze_recovered_p1 as p1_recovery

ROOT=Path(__file__).resolve().parents[1]

class HistoricalCausalAuditTests(unittest.TestCase):
    def test_recovered_first_archive_integrity_does_not_rescue_failed_replay(self):
        result=p1_recovery.analyze()
        self.assertEqual(result['P1.7']['archive_members'],35)
        self.assertEqual(result['P1.7']['original_verdict']['verdict'],'FAIL')
        self.assertEqual(result['P1.7']['original_replay_exit_code'],1)
        self.assertEqual(result['P1.7']['unique_accepted'],8)
        self.assertEqual(result['P1.7']['ambiguous_accepted'],0)
        self.assertEqual(result['new_model_calls'],0)
        self.assertEqual(result['P1.11.1_threshold_diagnosis']['threshold_only_correctness_ceiling'],6)
        self.assertTrue(result['P1.11.1_threshold_diagnosis']['threshold_only_cannot_reach_registered_floor'])

    def test_recovered_archive_mutation_is_rejected(self):
        with TemporaryDirectory() as d:
            path=Path(d)/'first.zip'
            path.write_bytes(b'not the historical first')
            with self.assertRaises(ValueError):p1_recovery.verify_p17(path)

    def test_recovered_format_and_meaning_are_distinct_and_first_outcomes_stay_frozen(self):
        result=p1_recovery.analyze()
        early=result['early_archives']
        self.assertEqual(len(early),6)
        self.assertEqual(sum(row['archive_members'] for row in early.values()),197)
        self.assertEqual(early['P1.5']['original_task_acceptance']['arithmetic_accepted'],4)
        self.assertEqual(early['P1.5']['original_task_acceptance']['csp_accepted'],0)
        self.assertEqual(early['P1.5']['format_diagnosis']['nonexecuted'],4)
        self.assertEqual(early['P1.6']['format_diagnosis']['nonexecuted'],7)
        stable=early['P1.2-validation']['score_diagnosis']
        self.assertTrue(stable['all_loo_winners_stable'])
        self.assertEqual(stable['original_compatible_routes'],10)
        self.assertEqual([row['task_id'] for row in stable['incompatible_planning_rows']],['p12v_09','p12v_12'])
        self.assertEqual(result['P1.3']['task_rows'],24)
        self.assertFalse(result['P1.3']['original_verdict']['answer_capability_validated'])
        self.assertFalse(result['P1.3']['original_verdict']['semantic_fallback_validated'])
        for study,row in result['current_model_free_replay_receipt']['result']['results'].items():
            self.assertEqual(row['exit_code'],0)
            self.assertEqual(row['result']['decision'],early[study]['original_verdict'])
            self.assertFalse(row['result']['model_inference'])

    def test_archive_identity_is_not_report_identity_in_cost_registry(self):
        with (ROOT/'research/audit/EXPERIMENT_REGISTRY.csv').open(encoding='utf-8-sig') as stream:
            rows={row['experiment_id']:row for row in csv.DictReader(stream)}
        archive=ROOT/'research/evidence/bp-certificate-2026-10-08/first.zip'
        report=archive.parent/'first-report.json'
        archive_sha=hashlib.sha256(archive.read_bytes()).hexdigest()
        report_sha=hashlib.sha256(report.read_bytes()).hexdigest()
        self.assertNotEqual(archive_sha,report_sha)
        self.assertEqual(rows['BP-Certificate-Economics']['evidence_archive_hash'],archive_sha)

    def test_linked_notion_version_page_without_project_name_is_included(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            project=root/'NEUMANN -- aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.md'
            project.write_text('<page url="https://app.notion.com/p/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb">v0.0.2 | Result</page>',encoding='utf-8')
            linked=root/'v0.0.2 -- bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.md';linked.write_text('Opened report')
            other=root/'v0.0.3 -- cccccccccccccccccccccccccccccccc.md';other.write_text('Unrelated project')
            found=registry.notion_document_candidates(root)
            self.assertIn(linked,found);self.assertNotIn(other,found)

    def test_linked_sealed_version_is_excluded_before_its_contents_are_read(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            project=root/'NEUMANN -- aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.md'
            project.write_text('<page url="https://app.notion.com/p/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb">v0.0.98 | Sealed</page>',encoding='utf-8')
            sealed=root/'v0.0.98 -- bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.md';sealed.write_text('Protected')
            with patch.object(registry,'safe_document',side_effect=lambda p: project.read_bytes() if p==project else (_ for _ in ()).throw(AssertionError('sealed read'))):
                self.assertNotIn(sealed,registry.notion_document_candidates(root))

    def test_exported_markdown_links_recover_the_actual_snapshot_format(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            project=root/'NEUMANN -- aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.md'
            project.write_text('[v0.0.2 | Report](v0.0.2%20--%20bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.md)',encoding='utf-8')
            linked=root/'v0.0.2 -- bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.md';linked.write_text('Opened report')
            self.assertIn(linked,registry.notion_document_candidates(root))

    def test_break_even_includes_startup_and_strict_inequality(self):
        self.assertEqual(audit.break_even(1,11,5,3),6)
        self.assertEqual(audit.break_even(11,1,5,3),1)
        self.assertIsNone(audit.break_even(1,11,3,3))
        self.assertIsNone(audit.break_even(1,11,2,3))

    def test_retained_certificate_geometry_is_not_a_new_optimization(self):
        with patch('scipy.optimize.linprog',side_effect=AssertionError('no new solves')), \
             patch('scipy.optimize.milp',side_effect=AssertionError('no new solves')):
            result=geometry.analyze()
        original=result['groups']['v088_opened_training']
        transfer=result['groups']['M106_opened_transfer']
        self.assertEqual(original['originals'],48)
        self.assertEqual(original['dual_nullities'],[0])
        self.assertEqual(transfer['originals'],16)
        self.assertEqual(transfer['dual_nullities'],[14,28,56,112])
        self.assertTrue(original['all_active_support_full_rank'])
        self.assertTrue(transfer['all_active_support_full_rank'])
        self.assertEqual(result['new_model_forwards'],0)
        self.assertEqual(result['decision'],'HOLD_LEARNING')

    def test_q34_source_reader_rejects_sealed_names_before_io(self):
        with patch.object(Path,'read_bytes',side_effect=AssertionError('no sealed reads')):
            with self.assertRaises(ValueError):q34.load_opened('v098_fresh_sources')
            with self.assertRaises(ValueError):q34.load_opened('v107_decision3')

    def test_q34_retained_attribution_does_not_grant_unexecuted_control_capability(self):
        result=q34.analyze()
        self.assertEqual(result['originals'],24)
        self.assertEqual(result['equivalent_views'],48)
        self.assertEqual(result['first_timed_original_witnesses_rechecked'],192)
        self.assertEqual(result['all_v102_support_dual_nullities'],[0])
        self.assertEqual(result['groups']['CHEAP_RESIDUAL_COVERAGE_ONLY']['top2m_covers_entire_positive_basis'],18)
        self.assertEqual(result['groups']['CHEAP_RESIDUAL_COVERAGE_ONLY']['top4m_covers_entire_positive_basis'],48)
        self.assertIsNone(result['groups']['CHEAP_RESIDUAL_COVERAGE_ONLY']['new_final_capability_or_cost'])
        for route in ('EXPAND4_s100001','EXPAND4_s100002'):
            self.assertTrue(result['groups'][route]['expansion_matches_missing_top2m'])
        self.assertEqual(result['new_performance_measurements'],0)

    def test_sealed_payload_cannot_enter_document_reader(self):
        with patch.object(Path,'read_bytes',side_effect=AssertionError('must reject before I/O')):
            with self.assertRaises(ValueError):registry.safe_document(ROOT/'private/decision3_sealed.json')

    def test_nested_verdict_does_not_treat_observation_acceptance_as_pass(self):
        o={'summary':{'decision':'FAIL'},'records':[{'accepted':True}],'observations':12}
        self.assertEqual(registry.nested_verdicts(o),{'summary.decision':'FAIL'})

    def test_unknown_independence_is_not_observation_count(self):
        with (ROOT/'research/audit/EXPERIMENT_REGISTRY.csv').open(encoding='utf-8-sig') as stream:
            rows=list(csv.DictReader(stream))
        by={r['experiment_id']:r for r in rows}
        self.assertEqual(len(rows),len(by))
        self.assertTrue(all(f'v0.0.{i}' in by for i in range(1,107)))
        self.assertEqual(by['v0.0.102']['number_of_independent_problems'],'24')
        self.assertEqual(by['v0.0.102']['number_of_observations'],'768')
        self.assertEqual(by['Structural-Experience']['number_of_independent_problems'],'')
        self.assertEqual(by['P1.10']['frozen_verdict'],'INCOMPLETE')
        self.assertEqual(by['P1.11']['frozen_verdict'],'NOT_EVALUATED')
        self.assertEqual(by['G0-Probabilistic-Native']['number_of_independent_problems'],'')
        self.assertEqual(by['G0-Probabilistic-Native']['number_of_observations'],'375')
        self.assertEqual(by['G0-Probabilistic-Native']['frozen_verdict'],
                         'INCOMPLETE; NO_REGISTERED_FAMILY_PASS; HOLD_LEARNING')
        self.assertEqual(by['Probabilistic-Analytic-Controls']['number_of_observations'],'')
        self.assertEqual(by['Probabilistic-Analytic-Controls']['total_cost'],'')

    def test_real_m106_cause_replay_cannot_call_optimizer(self):
        path=ROOT/'docs/experiments/results/m106_bp_transfer_first/report.json'
        before=hashlib.sha256(path.read_bytes()).hexdigest()
        with patch('scipy.optimize.linprog',side_effect=AssertionError('no new solves')):
            result=audit.m106()
        self.assertEqual(result['checks']['final_accepted'],256)
        self.assertEqual(result['checks']['restricted_original_accepted'],8)
        # Count first timed0 only, not both warmup0 and timed0.
        self.assertEqual(result['first_timed_repeat_factor_counts']['4']['attempts'],32)
        self.assertEqual(result['checks']['offline_existing_native_dual_pair_checks'],19)
        self.assertEqual(result['checks']['offline_existing_native_dual_pair_accepted'],19)
        self.assertEqual(result['first_timed_optimal_primal_rejected_paths'],13)
        self.assertEqual(result['first_timed_optimal_primal_rejected_originals'],7)
        self.assertEqual(result['new_solver_calls'],0)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)

    def test_original_source_mutation_rejected(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'opened.json.gz';p.write_bytes(b'not original')
            with self.assertRaises(Exception):
                audit.verify_source(p,{'gzip_sha256':'0'*64,'json_sha256':'0'*64})

    def test_censored_direct_has_no_speedup_or_break_even(self):
        with (ROOT/'research/audit/LP_SUCCESS_ENVELOPE.csv').open(encoding='utf-8-sig') as stream:
            rows=list(csv.DictReader(stream))
        unavailable=[r for r in rows if r['direct_capable']=='False']
        self.assertEqual(len(rows),192);self.assertEqual(len(unavailable),16)
        for r in unavailable:
            self.assertEqual(r['S_registered_ms'],'')
            self.assertEqual(r['registered_candidate_direct_ratio'],'')
            self.assertEqual(r['N_break_even_same_case'],'')

    def test_break_even_subtracts_full_query_not_post_only(self):
        with (ROOT/'research/audit/LP_SUCCESS_ENVELOPE.csv').open(encoding='utf-8-sig') as stream:
            rows=list(csv.DictReader(stream))
        report=json.loads((ROOT/'docs/experiments/results/q5_first_evaluation/report.json').read_bytes())
        costs={(r['case_id'],r['route']):r for r in report['summary']['case_costs']}
        for row in rows:
            c=costs[row['case_id'],row['route']]
            self.assertAlmostEqual(float(row['candidate_cold_plus_investment_ms'])+
                                   float(row['candidate_observed_operational_ms']),c['cold_q1_ms'])

if __name__=='__main__':unittest.main()
