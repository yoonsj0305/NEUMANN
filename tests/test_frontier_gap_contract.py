"""Synthetic receipt/adapter fault fixtures, NOT model or frontier evidence."""
import copy
import importlib.util
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('_frontier_stdlib',ROOT/'neumann1/frontier_gap_contract.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


def trace_payload(row):
    keys=('task_id','role','repeat','system_id','system_revision','problem_sha256',
          'answer_sha256','manifest_sha256','complete')
    return {**{k:row[k] for k in keys},'all_stages_retained':True,
        'resources':{k:{n:v[n] for n in ('value','status','unit')} for k,v in row['resources'].items()}}


def rebind_trace(row,blobs):
    raw=json.dumps(trace_payload(row),sort_keys=True).encode();ref=c.digest(raw);blobs[ref]=raw
    row['trace_sha256']=ref
    for value in row['resources'].values():value['trace_sha256']=ref


def fixture(*,small_pass=False,thresholds=None):
    units={'compute':'fixture_ops','ram_bytes':'bytes','vram_bytes':'bytes',
           'latency_ms':'ms','energy_j':'J','cost':'USD'}
    blobs={};tasks=[]
    for i,family in enumerate(('algebra_fixture','planning_fixture','easy_fixture')):
        raw=('synthetic original task '+str(i)).encode();ref=c.digest(raw);blobs[ref]=raw
        tasks.append({'id':str(i),'family':family,'split':'fresh_evaluation','problem_sha256':ref,
                      'source':'author_synthetic_fixture','license':'fixture_only_no_dataset_claim'})
    m={'schema':'neumann.frontier-gap.manifest.v1','question_namespace':c.NAMESPACE,
       'frozen_head':'a'*40,'verifier_id':'fixture_original_checker',
       'candidate_input_policy':'original_task_only','gap_membership':'small_and_frontier_only',
       'new_fitting':False,'repeats':2,'tasks':tasks,
       'systems':{r:{'id':r+'_fixture','revision':'fixture_v1','tools':['same_fixture_tool'],
                    'budget':{'max_calls':10,'max_cost':1000.,'max_latency_ms':1000.}} for r in c.ROLES},
       'metric_units':units,'compute_metric':'fixture_operations_not_real_FLOPs',
       'accounting_policy':'synthetic_complete_fixture_no_real_execution_claim',
       'cold_start_policy':'fixture_charged','investment_accounting':'fixture_no_investment',
       'thresholds':{'small_success_max':0.,'frontier_success_min':1.,'neumann_success_min':1.,
          'quality_delta_max':0.,'min_gap_cases':2,'min_gap_families':2,
          'resource_ratio_max':{k:.5 for k in c.METRICS}}}
    if thresholds:m['thresholds'].update(thresholds)
    rows=[]
    for t in tasks:
        for role in c.ROLES:
            for repeat in range(2):
                answer=b'valid' if role!='small' or t['id']=='2' or small_pass else b'invalid'
                ref=c.digest(answer);blobs[ref]=answer
                row={'task_id':t['id'],'role':role,'repeat':repeat,'manifest_sha256':c.manifest_digest(m),
                     'problem_sha256':t['problem_sha256'],'answer_sha256':ref,'complete':True,
                     'system_id':m['systems'][role]['id'],'system_revision':'fixture_v1',
                     'resources':{k:{'status':'measured','value':40. if role=='neumann' else 100.,'unit':units[k]} for k in c.METRICS}}
                rebind_trace(row,blobs);rows.append(row)
    return m,rows,blobs


def verifier(problem,answer,identity):
    assert identity=='fixture_original_checker'
    return answer==b'valid'


def trace_checker(raw,row,manifest):
    return json.loads(raw)==trace_payload(row)


def run(data,**kwargs):
    return c.audit(*data,verify_original=kwargs.get('verify_original',verifier),
                   validate_trace=kwargs.get('validate_trace',trace_checker))


class FrontierGapTests(unittest.TestCase):
    def test_gap_comes_from_actual_verified_pair_outcomes_only(self):
        result=run(fixture())
        self.assertEqual(result['gap_task_ids'],['0','1'])
        self.assertEqual(result['observations'],18)
        self.assertEqual(result['failed_original_verifications'],4)
        self.assertEqual(result['decision'],'CASE_SET_GATE_PASSED_NOT_GLOBAL_CLOSURE')
        self.assertEqual(set(result['global_questions'].values()),{'OPEN'})

    def test_no_gap_does_not_prove_frontier_equivalence(self):
        self.assertEqual(run(fixture(small_pass=True))['decision'],'NO_VERIFIED_FRONTIER_GAP')

    def test_neumann_failure_cannot_change_gap_or_emit_iso_ratio(self):
        data=fixture();m,rows,blobs=data;row=next(r for r in rows if r['role']=='neumann')
        bad=b'bad answer';row['answer_sha256']=c.digest(bad);blobs[c.digest(bad)]=bad;rebind_trace(row,blobs)
        result=run(data)
        self.assertEqual(result['gap_task_ids'],['0','1'])
        self.assertEqual(result['decision'],'CAPABILITY_UNREACHED_NO_ISO_CAPABILITY_CLAIM')
        self.assertTrue(all(x is None for x in result['resource_ratios'].values()))

    def test_receipt_accepted_flag_is_not_original_verification(self):
        data=fixture()
        for row in data[1]:row['accepted']=True
        self.assertEqual(run(data)['gap_task_ids'],['0','1'])

    def test_verifier_error_is_not_proven_small_baseline_failure(self):
        def broken(problem,answer,identity):
            if answer==b'invalid':raise RuntimeError('checker failed')
            return True
        result=run(fixture(),verify_original=broken)
        self.assertEqual(result['gap_task_ids'],[])
        self.assertEqual(len(result['verification_errors']),4)

    def test_nonboolean_verifier_rejected(self):
        with self.assertRaises(ValueError):run(fixture(),verify_original=lambda *args:'accepted')

    def test_missing_or_duplicate_failed_observations_rejected(self):
        for mode in ('missing','duplicate'):
            m,rows,blobs=fixture()
            if mode=='missing':rows.pop(0)
            else:rows.append(copy.deepcopy(rows[0]))
            with self.assertRaises(ValueError):run((m,rows,blobs))

    def test_original_identity_and_model_revision_enforced(self):
        for key,value in (('problem_sha256','0'*64),('system_revision','post_result_swap')):
            data=fixture();data[1][0][key]=value
            with self.assertRaises(ValueError):run(data)

    def test_replaced_answer_or_trace_artifact_rejected(self):
        for key in ('answer_sha256','trace_sha256'):
            data=fixture();data[2][data[1][0][key]]=b'replaced'
            with self.assertRaises(ValueError):run(data)

    def test_execution_trace_must_validate_complete_attempt_costs(self):
        data=fixture();data[1][0]['resources']['cost']['value']=0.
        with self.assertRaisesRegex(ValueError,'provenance rejected'):run(data)
        with self.assertRaises(ValueError):run(fixture(),validate_trace=lambda *args:False)

    def test_unknown_is_not_zero_or_measured(self):
        data=fixture();row=next(r for r in data[1] if r['role']=='frontier')
        row['resources']['energy_j'].update(status='unavailable',value=None);rebind_trace(row,data[2])
        result=run(data)
        self.assertIsNone(result['resource_ratios']['energy_j'])
        self.assertEqual(result['decision'],'PARTIAL_RESOURCE_EVIDENCE_NO_FULL_NORTH_STAR_CLAIM')
        row['resources']['energy_j']['value']=0.
        with self.assertRaisesRegex(ValueError,'unknown is not zero'):run(data)

    def test_estimated_compute_cannot_be_a_measured_FLOPs_claim(self):
        data=fixture();row=next(r for r in data[1] if r['role']=='frontier')
        row['resources']['compute']['status']='estimated';rebind_trace(row,data[2])
        result=run(data)
        self.assertEqual(result['resource_status']['compute'],'estimated')
        self.assertIsNone(result['resource_ratios']['compute'])

    def test_incompatible_units_and_nonfinite_values_rejected(self):
        for value in (-1.,math.nan,True):
            data=fixture();data[1][0]['resources']['compute']['value']=value
            with self.assertRaises(ValueError):run(data)
        data=fixture();data[1][0]['resources']['energy_j']['unit']='tokens'
        with self.assertRaisesRegex(ValueError,'units'):run(data)

    def test_per_family_failure_cannot_be_pooled_away(self):
        data=fixture(thresholds={'neumann_success_min':.5,'quality_delta_max':.5})
        for row in data[1]:
            if row['role']=='neumann' and row['task_id']=='1':
                raw=b'invalid';row['answer_sha256']=c.digest(raw);data[2][c.digest(raw)]=raw;rebind_trace(row,data[2])
        self.assertEqual(run(data)['decision'],'CAPABILITY_UNREACHED_NO_ISO_CAPABILITY_CLAIM')

    def test_zero_frontier_denominator_has_no_saving_ratio(self):
        data=fixture()
        for row in data[1]:
            row['resources']['vram_bytes']['value']=0.;rebind_trace(row,data[2])
        result=run(data)
        self.assertIsNone(result['resource_ratios']['vram_bytes'])
        self.assertEqual(result['decision'],'PARTIAL_RESOURCE_EVIDENCE_NO_FULL_NORTH_STAR_CLAIM')

    def test_measured_resource_failure_is_not_a_pass(self):
        data=fixture()
        for row in data[1]:
            if row['role']=='neumann':row['resources']['cost']['value']=90.;rebind_trace(row,data[2])
        self.assertEqual(run(data)['decision'],'MEASURED_RESOURCE_GATE_FAILED')

    def test_equal_tools_fresh_split_and_no_oracle_policy_enforced(self):
        data=fixture();data[0]['systems']['small']['tools']=[]
        with self.assertRaises(ValueError):run(data)
        data=fixture();data[0]['tasks'][0]['split']='opened_development'
        with self.assertRaises(ValueError):run(data)
        data=fixture();data[0]['candidate_input_policy']='frontier_solution'
        with self.assertRaises(ValueError):run(data)

    def test_resource_failure_in_one_family_cannot_be_pooled_away(self):
        data=fixture()
        for row in data[1]:
            if row['role']=='neumann':
                row['resources']['cost']['value']=10. if row['task_id']=='0' else 70.
                rebind_trace(row,data[2])
        result=run(data)
        self.assertAlmostEqual(result['resource_ratios']['cost'],.4)
        self.assertEqual(result['decision'],'MEASURED_RESOURCE_GATE_FAILED')

    def test_peak_memory_is_not_a_sum_of_sequential_queries(self):
        result=run(fixture())
        self.assertEqual(result['resource_totals']['frontier']['ram_bytes'],100.)
        self.assertEqual(result['resource_totals']['neumann']['vram_bytes'],40.)

    def test_budget_source_and_accounting_cannot_be_omitted(self):
        for key,value in (('max_calls',True),('max_cost',-1.),('max_latency_ms',0.)):
            data=fixture();data[0]['systems']['small']['budget'][key]=value
            with self.assertRaises(ValueError):run(data)
        for field in ('source','license'):
            data=fixture();data[0]['tasks'][0][field]=''
            with self.assertRaises(ValueError):run(data)
        data=fixture();data[0]['cold_start_policy']=''
        with self.assertRaises(ValueError):run(data)

    def test_frozen_question_namespace_and_import_purity(self):
        self.assertEqual(c.QUESTIONS['Q5'],'complete_end_to_end_less_than_direct')
        self.assertEqual(c.QUESTIONS['Q6'],'unseen_open_set_scaling_transfer')
        self.assertEqual(len(c.QUESTIONS),7)
        code="import importlib.util,sys; s=importlib.util.spec_from_file_location('pure_contract','neumann1/frontier_gap_contract.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); assert not any(n in sys.modules for n in ('numpy','scipy','torch','highspy'))"
        p=subprocess.run([sys.executable,'-c',code],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)

    def test_duplicate_original_cannot_inflate_case_or_family_coverage(self):
        data=fixture()
        data[0]['tasks'][1]['problem_sha256']=data[0]['tasks'][0]['problem_sha256']
        with self.assertRaisesRegex(ValueError,'duplicate original'):run(data)

    def test_undefined_family_ratio_is_partial_evidence_not_a_measured_failure(self):
        data=fixture()
        for row in data[1]:
            if row['task_id']=='0':
                row['resources']['vram_bytes']['value']=0.;rebind_trace(row,data[2])
        result=run(data)
        self.assertAlmostEqual(result['resource_ratios']['vram_bytes'],.4)
        self.assertIsNone(result['family_cells'][0]['resource_ratios']['vram_bytes'])
        self.assertEqual(result['decision'],'PARTIAL_RESOURCE_EVIDENCE_NO_FULL_NORTH_STAR_CLAIM')


if __name__=='__main__':unittest.main()
