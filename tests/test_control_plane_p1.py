"""P1 synthetic wiring, accounting, leakage and fault contracts only."""
import ast
import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from neumann1.control_plane_v1 import ROUTES, ScoreFailure, ScoreResult, digest
from neumann1.control_plane_scoring_v1 import ChoiceScorer
from neumann1.control_plane_p1_contract import MODEL, TASK_IDS, PUBLIC_SHA256, evaluate, manifest, validate_identity
from experiments.control_plane_p1_first import ROOT, PUBLIC, forbid_generation, registered_sources, run_study, score_task
from experiments.control_plane_p1_replay import replay


class Backend:
    def __init__(self, fail=False, winner=0):
        self.batch_size = 4
        self.calls = 0
        self.fail = fail
        self.winner = winner
    def forward_bound(self, plan):
        return len(plan.rows) // self.batch_size
    def evaluate(self, plan, remaining_ms):
        self.calls += 1
        if self.fail:
            raise ScoreFailure("synthetic partial forward", 1, 12, 5)
        scores = {r:-float(i+1) for i,r in enumerate(ROUTES)}
        if self.winner:
            scores[ROUTES[0]], scores[ROUTES[self.winner]] = scores[ROUTES[self.winner]], scores[ROUTES[0]]
        matrix = (tuple(scores[label] for label in plan.labels),)
        pad = 4 * max(len(r.prompt_ids)+len(r.label_ids) for r in plan.rows)
        return ScoreResult(matrix, self.forward_bound(plan), pad, 1234)


def scorer(backend=None):
    return ChoiceScorer(lambda s:[1,2], lambda s:[3], backend or Backend(),
                        {"weights_frozen":True,"evidence_kind":"synthetic_contract_fixture"})


def ledger():
    return {"evaluated_tokens":0,"padded_tokens":0,"forward_calls":0,"score_rows":0,"scored_tokens":0,
            "remaining_study_ms":lambda:1000000}


def records(degenerate=False):
    result=[]
    for i,task_id in enumerate(TASK_IDS):
        scores = [-1.,-3.,-4.,-5.] if degenerate or i<6 else [-3.,-1.,-4.,-5.]
        result.append({"task_id":task_id,"status":"COMPLETE","complete_ms":1.,"canonical_scores":scores,
                       "max_batch_delta_nats":0.,"max_order_delta_nats":0.,"stable_large_margin_winner":True})
    return result


def archive_fixture(directory):
    """Synthetic receipts only: never register these as actual Gemma evidence."""
    rows=json.loads(PUBLIC.read_bytes())['rows']
    state=ledger()
    observations=[score_task(row,scorer(Backend(winner=i//6)),state) for i,row in enumerate(rows)]
    identity={**MODEL,'device_type':'cuda','device_name':'Tesla T4','evidence_kind':'actual_frozen_model',
              'framework':'torch-2.11.0+cu128/transformers-5.16.1','torchvision':'0.26.0+cu128'}
    values={'manifest.json':{'registration':{'contract':manifest()},'public_rows':rows},
            'core.json':identity,'scorer.json':identity,
            'report.json':{'status':'COMPLETE','generated_calls':0,'tool_calls':0,
                'ledger':{k:v for k,v in state.items() if not callable(v)},'core_audit':{'unchanged':True},
                'whole_study_ms':100,'accounting_complete':True,
                'decision':evaluate(observations,{'unchanged':True},0,100,True)}}
    values.update({'task_%02d.json'%i:record for i,record in enumerate(observations)})
    for name,value in values.items():(directory/name).write_text(json.dumps(value))
    repin(directory)


def repin(directory):
    """Rehash tampered synthetic fixture to exercise semantic checks too."""
    terminal={'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.glob('*.json')
                       if p.name!='terminal.json'},'no_replacement':True,'complete':True,'decision':'PASS'}
    (directory/'terminal.json').write_text(json.dumps(terminal))


class P1Contracts(unittest.TestCase):
    def test_original_public_only_dataset_same_hash(self):
        data=json.loads(PUBLIC.read_bytes())
        self.assertEqual(digest([r['view'] for r in data['rows']]),PUBLIC_SHA256)
        self.assertEqual(tuple(r['task_id'] for r in data['rows']),TASK_IDS)
        self.assertTrue(all(set(r)=={'task_id','view'} for r in data['rows']))
        self.assertTrue(all(set(r['view'])=={'instruction','public'} for r in data['rows']))
        # Compare exact public export against authoritative opened tasks in full CI.
        source=ast.parse((ROOT/'experiments/general_multiplier_tasks.py').read_text())
        fn=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='multiplier_tasks')
        pairs=ast.literal_eval(next(n for n in fn.body if isinstance(n,ast.Return)).value)
        self.assertEqual([r['view'] for r in data['rows']],
                         [{'instruction':t['instruction'],'public':t['public']} for t,_ in pairs])

    def test_registration_freezes_sources_and_contract(self):
        registration,rows=registered_sources()
        self.assertEqual(len(rows),12)
        self.assertIn('neumann1/control_plane_scoring_v1.py',registration['source_sha256'])

    def test_three_modes_keep_exact_costs_and_order_independence(self):
        state=ledger();s=scorer()
        row=json.loads(PUBLIC.read_bytes())['rows'][0]
        result=score_task(row,s,state)
        self.assertEqual(result['status'],'COMPLETE')
        self.assertEqual(result['max_batch_delta_nats'],0)
        self.assertEqual(result['max_order_delta_nats'],0)
        self.assertEqual(state['forward_calls'],6)
        self.assertEqual(state['score_rows'],12)
        self.assertEqual(state['evaluated_tokens'],36)
        self.assertEqual(state['padded_tokens'],36)
        self.assertEqual(s.backend.batch_size,4)

    def test_generation_tripwire_counts_and_blocks_both_paths(self):
        core=SimpleNamespace(model=SimpleNamespace())
        counter=forbid_generation(core)
        self.assertEqual(counter['calls'],0)
        with self.assertRaisesRegex(RuntimeError,'generation forbidden'):core.generate()
        with self.assertRaisesRegex(RuntimeError,'generation forbidden'):core.model.generate()
        self.assertEqual(counter['calls'],2)

    def test_private_family_and_answer_leakage_rejected_before_scoring(self):
        for key in ('family','id','private','exact'):
            s=scorer();row={'task_id':'meta','view':{'instruction':'visible','public':{'x':1},key:'HIDDEN_GOLD_SENTINEL'}}
            with self.assertRaises(ValueError):score_task(row,s,ledger())
            self.assertEqual(s.backend.calls,0)

    def test_partial_forward_retained_and_fail_closed(self):
        state=ledger();row=json.loads(PUBLIC.read_bytes())['rows'][0]
        result=score_task(row,scorer(Backend(True)),state)
        self.assertEqual(result['status'],'FAILED')
        self.assertEqual(result['passes'][0]['status'],'STARTED')
        self.assertEqual(result['passes'][0]['known_partial_forward_calls'],1)
        self.assertEqual(state['forward_calls'],1)

    def test_admission_blocks_before_backend(self):
        state=ledger();state['forward_calls']=72
        s=scorer();row=json.loads(PUBLIC.read_bytes())['rows'][0]
        result=score_task(row,s,state)
        self.assertEqual(result['status'],'FAILED')
        self.assertEqual(s.backend.calls,0)

    def test_identity_exactness_and_synthetic_exclusion(self):
        good={**MODEL,'device_type':'cuda','device_name':'Tesla T4','evidence_kind':'actual_frozen_model',
              'framework':'torch-2.11.0+cu128/transformers-5.16.1','torchvision':'0.26.0+cu128'}
        validate_identity(good)
        for key,value in [('precision','float16'),('model_revision','other'),('artifact_sha256','0'*64),
                          ('tokenizer_sha256','0'*64),('evidence_kind','synthetic_contract_fixture'),('device_name','CPU')]:
            with self.assertRaises(ValueError):validate_identity(dict(good,**{key:value}))

    def test_nondegenerate_pass_does_not_open_capability_or_decision3(self):
        verdict=evaluate(records(),{'unchanged':True},0,100,True)
        self.assertEqual(verdict['verdict'],'PASS')
        self.assertTrue(verdict['p2_admitted'])
        self.assertFalse(verdict['decision3_admitted'])
        self.assertEqual(verdict['general_capability_gate'],'NOT_EVALUATED')

    def test_degenerate_and_numerically_inconsistent_scores_fail(self):
        self.assertEqual(evaluate(records(True),{'unchanged':True},0,100,True)['reason'],'DEGENERATE_ROUTE_SELECTION')
        data=records();data[0]['max_batch_delta_nats']=.051
        self.assertEqual(evaluate(data,{'unchanged':True},0,100,True)['verdict'],'FAIL')
        data=records();data[0]['stable_large_margin_winner']=False
        self.assertEqual(evaluate(data,{'unchanged':True},0,100,True)['verdict'],'FAIL')

    def test_invalid_accounting_identity_coverage_and_nan_never_pass(self):
        self.assertEqual(evaluate(records(),{'unchanged':False},0,100,True)['verdict'],'NOT_EVALUATED')
        self.assertEqual(evaluate(records(),{'unchanged':True},1,100,True)['verdict'],'FAIL')
        self.assertEqual(evaluate(records()[:11],{'unchanged':True},0,100,True)['verdict'],'NOT_EVALUATED')
        data=records();data[0]['canonical_scores'][0]=math.nan
        with self.assertRaises(ValueError):evaluate(data,{'unchanged':True},0,100,True)

    def test_first_failed_setup_retained_and_directory_not_reusable(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'first'
            with patch('experiments.control_plane_p1_first.subprocess.check_output',return_value='f'*40),\
                 patch('experiments.control_plane_p1_first.subprocess.run'):
                def fail():raise RuntimeError('synthetic model-load failure')
                result=run_study(target,'f'*40,core_factory=fail)
            self.assertEqual(result['status'],'INCOMPLETE')
            self.assertEqual(result['decision']['verdict'],'NOT_EVALUATED')
            self.assertTrue((target/'terminal.json').exists())
            self.assertFalse(replay(target)['complete'])
            with self.assertRaises(FileExistsError):run_study(target,'f'*40,core_factory=fail)

    def test_model_free_replay_recomputes_complete_costs_and_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);archive_fixture(directory)
            result=replay(directory)
            self.assertTrue(result['complete'])
            self.assertEqual(result['scoring_rows'],144)
            self.assertEqual(result['decision']['verdict'],'PASS')
            self.assertFalse(result['model_inference'])
            self.assertFalse(result['decision3_admitted'])

    def test_replay_detects_byte_corruption_missing_receipt_and_cost_drift(self):
        for mutation in ('bytes','missing','cost'):
            with tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp);archive_fixture(directory)
                target=directory/'task_00.json'
                if mutation=='bytes':target.write_text(target.read_text()+' ')
                elif mutation=='missing':target.unlink()
                else:
                    value=json.loads((directory/'report.json').read_bytes())
                    value['ledger']['evaluated_tokens']+=1
                    (directory/'report.json').write_text(json.dumps(value));repin(directory)
                with self.assertRaises(ValueError):replay(directory)

    def test_replay_rejects_cached_stability_and_public_input_drift(self):
        for mutation in ('stable','public'):
            with tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp);archive_fixture(directory)
                target=directory/('task_00.json' if mutation=='stable' else 'manifest.json')
                value=json.loads(target.read_bytes())
                if mutation=='stable':value['stable_large_margin_winner']=False
                else:value['public_rows'][0]['view']['instruction']='changed input'
                target.write_text(json.dumps(value));repin(directory)
                with self.assertRaises(ValueError):replay(directory)


if __name__=='__main__':unittest.main()
