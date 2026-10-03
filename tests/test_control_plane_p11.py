"""Synthetic P1.1 algebra, causal scoring and failure contracts; no Gemma inference."""
import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from neumann1.control_plane_v1 import ROUTES, digest
from neumann1.control_plane_p1_contract import MODEL, TASK_IDS
from neumann1.control_plane_p11 import (Budget,CODES,SCHEDULES,CodePlan,CodedFailure,NextCodeBackend,
    aggregate,audit_codes,contract,evaluate_development,plan_cost,prompt_for,score_development,validate_schedules)
from experiments.control_plane_p11_dev import PUBLIC,registration,run
from experiments.control_plane_p11_replay import replay

try:import torch
except ImportError:torch=None


def synthetic_matrix(utilities=(4.,1.,2.,3.),bias=(0.,20.,-10.,-30.)):
    # Log-softmax fixture with arbitrarily severe code prior. Not model evidence.
    rows=[]
    for mapping in [m for group in SCHEDULES for m in group]:
        logits=[utilities[mapping.index(c)]+bias[c] for c in range(4)]
        maximum=max(logits);norm=maximum+math.log(math.fsum(math.exp(v-maximum) for v in logits))
        rows.append([v-norm for v in logits])
    return rows


class FixtureBackend:
    def __init__(self,utilities=(4.,1.,2.,3.),partial=False):
        self.matrix=synthetic_matrix(utilities);self.calls=0;self.partial=partial
    def evaluate(self,plan,size,remaining):
        self.calls+=1;cost=plan_cost(plan,size)
        if self.partial:raise CodedFailure('synthetic forward fault',cost,1.)
        return {'scores':[self.matrix[p[-1]] for p in plan.prefixes],'cost':cost,'peak_accelerator_memory_bytes':1234}


def encode(prompt):
    # Decode the synthetic legend to identify its mapping; ignores problem IDs.
    legend=json.loads(prompt.split('\n')[1])['legend']
    mapping=tuple(next(i for i,item in enumerate(legend) if item['executor']==route) for route in ROUTES)
    index=[m for group in SCHEDULES for m in group].index(mapping)
    return [8,9,index]


def ledger():return {k:0 for k in ('input_rows','score_rows','scored_tokens','evaluated_tokens','padded_tokens','forward_calls')}


def fixture_records():
    rows=json.loads(PUBLIC.read_bytes())['rows'];state=ledger();records=[]
    for i,row in enumerate(rows):
        utility=(4.,1.,2.,3.) if i<6 else (1.,2.,3.,4.)
        record=score_development(row['view'],encode,[1,2,3,4],FixtureBackend(utility),state,lambda:100000)
        record['task_id']=row['task_id'];records.append(record)
    return records,state


def synthetic_archive(directory):
    records,state=fixture_records();rows=json.loads(PUBLIC.read_bytes())['rows']
    identity={**MODEL,'device_type':'cuda','device_name':'Tesla T4','evidence_kind':'actual_frozen_model',
              'framework':'torch-2.11.0+cu128/transformers-5.16.1','torchvision':'0.26.0+cu128'}
    values={'manifest.json':{'registration':{'contract':contract()},'public_rows':rows},'core.json':identity,
            'code_audit.json':{'codes':list(CODES),'token_ids':[1,2,3,4],'single_token':True,'special_tokens':False,
                               'tokenizer_sha256':MODEL['tokenizer_sha256']},
            'report.json':{'status':'COMPLETE','generated_calls':0,'tool_calls':0,'ledger':state,
                          'core_audit':{'unchanged':True},'accounting_complete':True,'controller_wall_ms':100,
                          'whole_study_ms':100,'decision':evaluate_development(records,True,True,0,100,100)}}
    values.update({'task_%02d.json'%i:r for i,r in enumerate(records)})
    for name,value in values.items():(directory/name).write_text(json.dumps(value))
    repin(directory)


def repin(directory):
    terminal={'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.glob('*.json')
                       if p.name!='terminal.json'},'complete':True,'no_replacement':True,'decision':'PASS'}
    (directory/'terminal.json').write_text(json.dumps(terminal))


class CodedContracts(unittest.TestCase):
    def test_balanced_distinct_maps_and_unbalanced_rejection(self):
        validate_schedules()
        for group in SCHEDULES:
            for route in range(4):self.assertEqual(sorted(m[route] for m in group),list(range(4)))
        with self.assertRaises(ValueError):validate_schedules((SCHEDULES[0],SCHEDULES[0]))
        broken=[list(g) for g in SCHEDULES];broken[0][0]=(0,0,1,2)
        with self.assertRaises(ValueError):validate_schedules(broken)

    def test_balancing_removes_fixed_additive_code_prior_without_fitting(self):
        matrix=synthetic_matrix();result=aggregate(matrix)
        self.assertTrue(all(max(range(4),key=lambda c:row[c])==1 for row in matrix))
        self.assertEqual(result['winner'],'DIRECT')
        self.assertAlmostEqual(result['scores']['DIRECT']-result['scores']['PYTHON'],1.)
        self.assertAlmostEqual(result['centered_schedule_delta_nats'],0.,places=10)
        unbiased=aggregate(synthetic_matrix(bias=(0,0,0,0)))
        for route in ROUTES:
            self.assertAlmostEqual(result['scores'][route]-result['scores']['DIRECT'],
                                   unbiased['scores'][route]-unbiased['scores']['DIRECT'])

    def test_nonadditive_mapping_interaction_is_not_assumed_cancelled(self):
        matrix=synthetic_matrix(bias=(0,0,0,0))
        for i,mapping in enumerate(SCHEDULES[1]):matrix[4+i][mapping[1]]+=1.5
        result=aggregate(matrix)
        self.assertGreater(result['centered_schedule_delta_nats'],.5)

    def test_nonfinite_and_missing_permutation_fail_closed(self):
        with self.assertRaises(ValueError):aggregate(synthetic_matrix()[:-1])
        matrix=synthetic_matrix();matrix[0][0]=math.nan
        with self.assertRaises(ValueError):aggregate(matrix)
        matrix=synthetic_matrix();matrix[0][0]=math.inf
        with self.assertRaises(ValueError):aggregate(matrix)

    def test_code_audit_requires_exact_vocabulary_single_non_special_unique_tokens(self):
        vocab={'A':1,'B':2,'C':3,'D':4};tokens={c:[i] for c,i in vocab.items()}
        tokenizer=SimpleNamespace(get_vocab=lambda:vocab,encode=lambda c,**kw:tokens[c],
                                  decode=lambda ids,**kw:next(c for c,i in vocab.items() if ids==[i]),all_special_ids=[])
        with patch('neumann1.control_plane_p11.MODEL',{**MODEL,'tokenizer_sha256':digest(vocab)}):
            self.assertEqual(audit_codes(tokenizer)['token_ids'],[1,2,3,4])
            tokens['A']=[1,2]
            with self.assertRaises(ValueError):audit_codes(tokenizer)
            tokens['A']=[1];tokenizer.all_special_ids=[1]
            with self.assertRaises(ValueError):audit_codes(tokenizer)
        with self.assertRaises(ValueError):audit_codes(tokenizer)

    def test_public_only_prompt_explicit_contracts_and_no_task_family(self):
        view={'instruction':'solve','public':{'x':3}}
        prompt=prompt_for(view,SCHEDULES[0][0]);self.assertIn('Bounded general Python',prompt)
        for key in ('private','family','id','exact'):
            with self.assertRaises(ValueError):prompt_for({**view,key:'HIDDEN'},SCHEDULES[0][0])

    def test_distinct_prefill_and_label_counts_three_modes_no_generation(self):
        state=ledger();view=json.loads(PUBLIC.read_bytes())['rows'][0]['view']
        result=score_development(view,encode,[1,2,3,4],FixtureBackend(),state,lambda:100000)
        self.assertEqual(result['status'],'COMPLETE');self.assertEqual(result['numeric_delta_nats'],0)
        self.assertEqual(state,{'input_rows':24,'score_rows':96,'scored_tokens':96,'evaluated_tokens':72,
                                'padded_tokens':72,'forward_calls':12})
        self.assertEqual(plan_cost(CodePlan(((1,2),(3,)),(4,5,6,7)),2)['padded_tokens'],4)

    def test_admission_and_partial_attempt_costs_preserved(self):
        view=json.loads(PUBLIC.read_bytes())['rows'][0]['view'];backend=FixtureBackend()
        state=ledger();state['forward_calls']=Budget().forward_calls
        result=score_development(view,encode,[1,2,3,4],backend,state,lambda:100000)
        self.assertEqual(result['status'],'FAILED');self.assertEqual(backend.calls,0)
        state=ledger();result=score_development(view,encode,[1,2,3,4],FixtureBackend(partial=True),state,lambda:100000)
        self.assertEqual(result['status'],'FAILED');self.assertEqual(state['forward_calls'],2)
        self.assertEqual(result['passes'][0]['status'],'STARTED')

    def test_development_pass_never_admits_p2_or_decision3(self):
        records,state=fixture_records();decision=evaluate_development(records,True,True,0,100,100)
        self.assertEqual(decision['verdict'],'PASS');self.assertFalse(decision['p2_admitted'])
        self.assertFalse(decision['decision3_admitted']);self.assertFalse(decision['fresh_validation_registered'])
        self.assertEqual(state['forward_calls'],144)
        self.assertEqual(evaluate_development(records[:11],True,True,0,100,100)['verdict'],'NOT_EVALUATED')
        self.assertEqual(evaluate_development(records,True,True,1,100,100)['verdict'],'FAIL')
        self.assertEqual(evaluate_development(records,True,True,0,180001,200000)['verdict'],'FAIL')

    def test_frozen_source_registration_and_original_fail_replay(self):
        self.assertEqual(len(registration()[1]),12)
        from experiments.control_plane_p1_replay import replay as replay_p1
        path=PUBLIC.parents[2]/'docs/experiments/results/control_plane_p1_first/p1'
        pins=json.loads((path.parent/'upload_pins.json').read_bytes())
        for name,pin in pins['files'].items():
            raw=(path.parent/name).read_bytes()
            self.assertEqual(len(raw),pin['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(),pin['sha256'])
        result=replay_p1(path)
        self.assertTrue(result['integrity_valid']);self.assertEqual(result['decision']['verdict'],'FAIL')
        self.assertEqual(result['decision']['winner_counts']['ARITHMETIC'],12)

    def test_startup_failure_retained_and_first_directory_exclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)/'first'
            from neumann1.control_plane_p1_contract import manifest
            def fail():raise RuntimeError('synthetic load fault; no model loaded')
            module=SimpleNamespace(FrozenAcceleratorCore=fail)
            with patch('experiments.control_plane_p11_dev.subprocess.check_output',return_value='f'*40),\
                 patch('experiments.control_plane_p11_dev.subprocess.run'),\
                 patch('experiments.control_plane_p11_dev.version',side_effect=lambda p:manifest()['runtime'][p]),\
                 patch.dict('sys.modules',{'experiments.general_multiplier_accelerator_core':module}):
                report=run(directory,'f'*40)
            self.assertEqual(report['status'],'INCOMPLETE')
            self.assertEqual(report['decision']['verdict'],'NOT_EVALUATED')
            self.assertIsNone(report['controller_wall_ms'])
            self.assertFalse(replay(directory)['complete'])
            with self.assertRaises(FileExistsError):run(directory,'f'*40)

    def test_replay_recomputes_costs_and_rejects_cached_summary_or_bytes(self):
        for mutation in (None,'byte','cost','summary'):
            with tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp);synthetic_archive(directory)
                if mutation=='byte':
                    with (directory/'task_00.json').open('a') as f:f.write(' ')
                elif mutation in ('cost','summary'):
                    path=directory/('report.json' if mutation=='cost' else 'task_00.json');value=json.loads(path.read_bytes())
                    if mutation=='cost':value['ledger']['input_rows']+=1
                    else:value['summary']['winner']='CSP'
                    path.write_text(json.dumps(value));repin(directory)
                if mutation:
                    with self.assertRaises(ValueError):replay(directory)
                else:
                    result=replay(directory);self.assertTrue(result['complete']);self.assertFalse(result['p2_admitted'])


@unittest.skipIf(torch is None,'optional CPU Torch contracts run in dedicated P1.1 CI')
class TensorContracts(unittest.TestCase):
    def model(self,fail=False):
        class Fixed(torch.nn.Module):
            def __init__(self):
                super().__init__();self.calls=0;self.generated=0
                self.table=torch.nn.Parameter(torch.tensor([[0.,2.,1.,-1.],[3.,0.,2.,1.],[-1.,1.,0.,3.],[2.,1.,0.,-1.]]),requires_grad=False)
            def generate(self,*args,**kwargs):self.generated+=1;raise AssertionError('no generation')
            def forward(self,input_ids,attention_mask,use_cache,logits_to_keep,return_dict):
                self.calls+=1
                if fail:raise RuntimeError('synthetic model fault')
                assert use_cache is False and return_dict
                return SimpleNamespace(logits=self.table[input_ids][:,logits_to_keep,:])
        return Fixed().eval()

    def test_single_prefill_next_code_matches_independent_causal_reference(self):
        model=self.model();plan=CodePlan(((1,2),(0,),(2,3,1)),(0,1,2,3))
        backend=NextCodeBackend(model,0,'cpu');batch=backend.evaluate(plan,3,10000)
        reference=[torch.log_softmax(model.table[p[-1]],dim=-1).tolist() for p in plan.prefixes]
        self.assertEqual(batch['scores'],[tuple(row) for row in reference])
        single=backend.evaluate(plan,1,10000);self.assertEqual(batch['scores'],single['scores'])
        self.assertEqual(batch['cost']['forward_calls'],1);self.assertEqual(batch['cost']['evaluated_tokens'],6)
        self.assertEqual(batch['cost']['score_rows'],12);self.assertEqual(batch['cost']['padded_tokens'],9)
        self.assertEqual(model.generated,0)

    def test_model_fault_charges_attempted_inputs_without_claiming_complete_scores(self):
        backend=NextCodeBackend(self.model(True),0,'cpu')
        with self.assertRaises(CodedFailure) as caught:backend.evaluate(CodePlan(((1,2),(3,)),(0,1,2,3)),2,10000)
        self.assertEqual(caught.exception.known_cost,{'input_rows':2,'score_rows':0,'scored_tokens':0,
                                                   'evaluated_tokens':3,'padded_tokens':4,'forward_calls':1})

    def test_parameter_mutation_or_training_rejects_before_forward(self):
        model=self.model();backend=NextCodeBackend(model,0,'cpu')
        model.train()
        with self.assertRaises(ValueError):backend.evaluate(CodePlan(((1,),),(0,1,2,3)),1,10000)
        model.eval()
        with torch.no_grad():model.table.add_(1)
        with self.assertRaises(ValueError):backend.evaluate(CodePlan(((1,),),(0,1,2,3)),1,10000)
        self.assertEqual(model.calls,0)


if __name__=='__main__':unittest.main()
