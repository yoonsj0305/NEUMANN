"""Full-S4 algebra and nontrivial sensitivity faults; synthetic, not Gemma."""
import base64
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from neumann1.control_plane_v1 import ROUTES, digest
from neumann1.control_plane_p1_contract import MODEL, manifest as p1_manifest
from neumann1.control_plane_p11 import SCHEDULES, aggregate as p11_aggregate
from neumann1.control_plane_p12 import (Budget, CODE_TOKEN_IDS, CodedFailure, CodePlan, NextCodeBackend,
    ORBITS, PERMUTATIONS, P11_FIRST_SHA256, aggregate, contract, evaluate_development, plan_cost,
    prompt_for, score_development, validate_group)
from experiments.control_plane_p12_dev import PUBLIC, registration, run
from experiments.control_plane_p12_replay import replay

try: import torch
except ImportError: torch = None


def matrix(utilities=(4.,1.,2.,3.), bias=(0.,20.,-10.,-30.)):
    rows = []
    for p in PERMUTATIONS:
        logits = [utilities[p.index(c)]+bias[c] for c in range(4)]
        maximum = max(logits); normalizer = maximum+math.log(math.fsum(math.exp(v-maximum) for v in logits))
        rows.append([v-normalizer for v in logits])
    return rows


def encode(prompt):
    legend = json.loads(prompt.split('\n')[1])['legend']
    p = tuple(next(i for i, item in enumerate(legend) if item['executor'] == route) for route in ROUTES)
    return [8,9,PERMUTATIONS.index(p)]


def ledger(): return {k:0 for k in ('input_rows','score_rows','scored_tokens','evaluated_tokens','padded_tokens','forward_calls')}


class Backend:
    def __init__(self, utilities=(4.,1.,2.,3.), partial=False):
        self.matrix = matrix(utilities); self.calls = 0; self.partial = partial
    def evaluate(self, plan, size, remaining):
        self.calls += 1; cost = plan_cost(plan,size)
        if self.partial: raise CodedFailure('synthetic fault',cost,1.)
        return {'scores':[self.matrix[p[-1]] for p in plan.prefixes], 'cost':cost,'peak_accelerator_memory_bytes':1234}


def records():
    state = ledger(); result = []; rows = json.loads(PUBLIC.read_bytes())['rows']
    for i, row in enumerate(rows):
        backend = Backend((4.,1.,2.,3.) if i < 6 else (1.,2.,3.,4.))
        r = score_development(row['view'],encode,CODE_TOKEN_IDS,backend,state,lambda:100000)
        r['task_id'] = row['task_id']; result.append(r)
    return result,state,rows


def repin(directory):
    report = json.loads((directory/'report.json').read_bytes())
    pins = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.glob('*.json') if p.name != 'terminal.json'}
    (directory/'terminal.json').write_text(json.dumps({'files':pins,'decision':report['decision']['verdict'],
        'complete':report['status'] == 'COMPLETE','no_replacement':True,'development_only':True}))


def archive(directory):
    rs,state,rows = records()
    values = {'manifest.json':{'registration':{'contract':contract()},'public_rows':rows},
        'core.json':{**MODEL,'device_type':'cuda','device_name':'Tesla T4','evidence_kind':'actual_frozen_model',
                     'framework':'torch-2.11.0+cu128/transformers-5.16.1','torchvision':'0.26.0+cu128'},
        'code_audit.json':{'codes':['A','B','C','D'],'token_ids':list(CODE_TOKEN_IDS),'single_token':True,
                           'special_tokens':False,'tokenizer_sha256':MODEL['tokenizer_sha256']},
        'report.json':{'schema':contract()['schema'],'status':'COMPLETE','generated_calls':0,'tool_calls':0,
            'ledger':state,'core_audit':{'unchanged':True},'accounting_complete':True,
            'controller_wall_ms':100,'whole_study_ms':100,'development_only':True,
            'historical_score_reuse':False,'fresh_validation_opened':False,
            'decision':evaluate_development(rs,True,True,0,100,100)}}
    values.update({'task_%02d.json'%i:r for i,r in enumerate(rs)})
    for name,value in values.items(): (directory/name).write_text(json.dumps(value))
    repin(directory)


class FullS4Contracts(unittest.TestCase):
    def test_group_is_exhaustive_disjoint_and_every_deletion_balanced(self):
        validate_group(); self.assertEqual(PERMUTATIONS,tuple(itertools.permutations(range(4))))
        self.assertEqual(sorted(i for orbit in ORBITS for i in orbit),list(range(24)))
        for orbit in ORBITS:
            for r in range(4): self.assertEqual(sorted(PERMUTATIONS[i][r] for i in orbit),list(range(4)))
        with self.assertRaises(ValueError): validate_group(PERMUTATIONS[:-1])
        with self.assertRaises(ValueError): validate_group(PERMUTATIONS,ORBITS[:-1])

    def test_extreme_fixed_code_prior_cancels_without_task_calibration(self):
        a = aggregate(matrix()); b = aggregate(matrix(bias=(0,0,0,0)))
        self.assertEqual(a['winner'],'DIRECT')
        for route in ROUTES:
            self.assertAlmostEqual(a['scores'][route]-a['scores']['DIRECT'],b['scores'][route]-b['scores']['DIRECT'])
        self.assertAlmostEqual(a['max_centered_loo_delta_nats'],0,places=10)

    def test_relabel_reindex_property_is_algebra_not_new_model_evidence(self):
        raw = matrix(); original = aggregate(raw)
        for relabel in PERMUTATIONS:
            transformed = [[None]*4 for _ in range(24)]
            for i,p in enumerate(PERMUTATIONS):
                q = tuple(relabel[c] for c in p); j = PERMUTATIONS.index(q)
                for c in range(4): transformed[j][relabel[c]] = raw[i][c]
            new = aggregate(transformed)
            for route in ROUTES: self.assertAlmostEqual(original['scores'][route],new['scores'][route])

    def test_interactions_can_remain_when_new_full_mean_gate_is_stable(self):
        raw = [[-50.+(4.,1.,2.,3.)[p.index(c)] for c in range(4)] for p in PERMUTATIONS]
        for i in ORBITS[0]: raw[i][PERMUTATIONS[i][0]] += 1.5
        result = aggregate(raw)
        self.assertGreater(result['max_centered_orbit_pair_delta_nats'],.5)
        self.assertLess(result['max_centered_loo_delta_nats'],.5)
        self.assertTrue(result['all_loo_winners_stable'])
        old = [raw[PERMUTATIONS.index(p)] for group in SCHEDULES for p in group]
        self.assertGreater(p11_aggregate(old)['centered_schedule_delta_nats'],.5)

    def test_large_orbit_effect_fails_nontrivial_new_gate_despite_same_winner(self):
        raw = [[-50.+(12.,0.,-2.,-4.)[p.index(c)] for c in range(4)] for p in PERMUTATIONS]
        for i in ORBITS[0]: raw[i][PERMUTATIONS[i][0]] += 12.
        result = aggregate(raw); self.assertTrue(result['all_loo_winners_stable'])
        self.assertGreater(result['max_centered_loo_delta_nats'],.5)
        rs,_,_ = records(); rs[0]['summary'] = result
        self.assertEqual(evaluate_development(rs,True,True,0,100,100)['reason'],'FULL_MEAN_ORBIT_SENSITIVITY')

    def test_missing_nonfinite_and_positive_probabilities_fail_closed(self):
        for value in (math.nan,math.inf,1.):
            raw = matrix(); raw[0][0] = value
            with self.assertRaises(ValueError): aggregate(raw)
        with self.assertRaises(ValueError): aggregate(matrix()[:-1])

    def test_all_three_modes_recompute_24_inputs_and_charge_exactly(self):
        row = json.loads(PUBLIC.read_bytes())['rows'][0]; state = ledger(); backend = Backend()
        result = score_development(row['view'],encode,CODE_TOKEN_IDS,backend,state,lambda:100000)
        self.assertEqual(result['status'],'COMPLETE'); self.assertEqual(backend.calls,3)
        self.assertEqual(state,{'input_rows':72,'score_rows':288,'scored_tokens':288,
                               'evaluated_tokens':216,'padded_tokens':216,'forward_calls':36})
        self.assertEqual(result['numeric_delta_nats'],0)
        with self.assertRaises(ValueError): prompt_for({**row['view'],'family':'HIDDEN'},PERMUTATIONS[0])

    def test_admission_caps_and_partial_costs_keep_incomplete_receipts(self):
        row = json.loads(PUBLIC.read_bytes())['rows'][0]; state = ledger(); backend = Backend()
        state['forward_calls'] = Budget().forward_calls
        result = score_development(row['view'],encode,CODE_TOKEN_IDS,backend,state,lambda:100000)
        self.assertEqual(result['status'],'FAILED'); self.assertEqual(backend.calls,0)
        state = ledger(); result = score_development(row['view'],encode,CODE_TOKEN_IDS,Backend(partial=True),state,lambda:100000)
        self.assertEqual(result['status'],'FAILED'); self.assertEqual(state['forward_calls'],6)
        self.assertEqual(result['passes'][0]['status'],'STARTED')

    def test_development_pass_never_admits_p2_or_fresh_validation(self):
        rs,state,_ = records(); decision = evaluate_development(rs,True,True,0,100,100)
        self.assertEqual(decision['verdict'],'PASS'); self.assertEqual(state['forward_calls'],432)
        self.assertFalse(decision['p2_admitted']); self.assertFalse(decision['decision3_admitted'])
        self.assertFalse(decision['fresh_validation_registered'])
        self.assertEqual(evaluate_development(rs[:11],True,True,0,100,100)['verdict'],'NOT_EVALUATED')
        self.assertEqual(evaluate_development(rs,True,True,1,100,100)['reason'],'GENERATION_FORBIDDEN')
        self.assertEqual(evaluate_development(rs,True,True,0,540001,600000)['reason'],'COMPLETE_COST_WALL_CAP')
        rs[0]['summary']['margin_nats'] = .5
        self.assertEqual(evaluate_development(rs,True,True,0,100,100)['reason'],'AMBIGUOUS_OR_UNSTABLE_FULL_MEAN_WINNER')

    def test_replay_recomputes_robustness_and_rejects_bytes_costs_and_admission(self):
        for mutation in (None,'byte','cost','summary','admission'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp); archive(path)
                if mutation == 'byte': (path/'task_00.json').write_bytes((path/'task_00.json').read_bytes()+b' ')
                elif mutation:
                    file = path/('task_00.json' if mutation == 'summary' else 'report.json'); value = json.loads(file.read_bytes())
                    if mutation == 'summary': value['summary']['max_centered_loo_delta_nats'] += 1
                    elif mutation == 'cost': value['ledger']['input_rows'] += 1
                    else: value['decision']['p2_admitted'] = True
                    file.write_text(json.dumps(value)); repin(path)
                if mutation:
                    with self.assertRaises(ValueError): replay(path)
                else: self.assertTrue(replay(path)['integrity_valid'])

    def test_startup_fault_retained_and_exclusive_first_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'first'
            def fail(): raise RuntimeError('synthetic load fault; no model')
            with patch('experiments.control_plane_p12_dev.subprocess.check_output',return_value='f'*40),\
                 patch('experiments.control_plane_p12_dev.subprocess.run'),\
                 patch('experiments.control_plane_p12_dev.version',side_effect=lambda p:p1_manifest()['runtime'][p]),\
                 patch.dict('sys.modules',{'experiments.general_multiplier_accelerator_core':SimpleNamespace(FrozenAcceleratorCore=fail)}):
                report = run(path,'f'*40)
            self.assertEqual(report['decision']['verdict'],'NOT_EVALUATED'); self.assertFalse(replay(path)['complete'])
            self.assertIsNone(report['controller_wall_ms'])
            with self.assertRaises(FileExistsError): run(path,'f'*40)

    def test_registration_exact_and_old_gate_unchanged(self):
        self.assertEqual(len(registration()[1]),12)
        from neumann1.control_plane_p11 import CRITERIA as old
        self.assertEqual(old['centered_schedule_tolerance_nats'],.5)
        self.assertFalse(contract()['historical_score_reuse'])

    def test_original_p11_zip_byte_identity_and_retained_fail_replay(self):
        path = PUBLIC.parents[2]/'docs/experiments/results/control_plane_p11_first.zip.b64'
        raw = base64.b64decode(path.read_bytes(),validate=True)
        self.assertEqual(len(raw),52833); self.assertEqual(hashlib.sha256(raw).hexdigest(),P11_FIRST_SHA256)
        with zipfile.ZipFile(io.BytesIO(raw)) as z,tempfile.TemporaryDirectory() as tmp:
            names = z.namelist(); self.assertEqual(len(names),36); self.assertEqual(len(set(names)),36)
            pins = json.loads(z.read('archive_manifest.json'))['members']
            self.assertEqual(set(pins),set(names)-{'archive_manifest.json'})
            for info in z.infolist():
                self.assertFalse(Path(info.filename).is_absolute()); self.assertNotIn('..',Path(info.filename).parts)
                self.assertFalse(stat.S_ISLNK(info.external_attr>>16))
                value = z.read(info.filename)
                if info.filename in pins:
                    self.assertEqual(hashlib.sha256(value).hexdigest(),pins[info.filename]['sha256'])
                    self.assertEqual(len(value),pins[info.filename]['bytes'])
                target = Path(tmp)/info.filename; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(value)
            from experiments.control_plane_p11_replay import replay as old_replay
            result = old_replay(Path(tmp)/'neumann_p11_first')
            self.assertTrue(result['integrity_valid']); self.assertEqual(result['decision']['verdict'],'FAIL')
            self.assertEqual(result['decision']['reason'],'NUMERIC_OR_PERMUTATION_INSTABILITY')


@unittest.skipIf(torch is None,'optional CPU Torch checked in dedicated P1.2 CI')
class FullS4Tensor(unittest.TestCase):
    def test_24_ragged_prefixes_use_last_causal_position_with_no_generation(self):
        class Model(torch.nn.Module):
            def __init__(self):
                super().__init__(); self.calls = 0
                self.table = torch.nn.Parameter(torch.arange(16,dtype=torch.float32).reshape(4,4),requires_grad=False)
            def generate(self,*a,**k): raise AssertionError('generation forbidden')
            def forward(self,input_ids,attention_mask,use_cache,logits_to_keep,return_dict):
                self.calls += 1; assert use_cache is False
                return SimpleNamespace(logits=self.table[input_ids][:,logits_to_keep,:])
        model = Model().eval(); backend = NextCodeBackend(model,0,'cpu')
        prefixes = tuple(tuple([i%4]*(i%3+1)) for i in range(24)); plan = CodePlan(prefixes,(0,1,2,3))
        batch = backend.evaluate(plan,4,10000); single = backend.evaluate(plan,1,10000)
        self.assertEqual(batch['scores'],single['scores']); self.assertEqual(model.calls,30)
        expected = [tuple(torch.log_softmax(model.table[p[-1]],dim=-1).tolist()) for p in prefixes]
        self.assertEqual(batch['scores'],expected); self.assertEqual(batch['cost']['score_rows'],96)


if __name__ == '__main__': unittest.main()
