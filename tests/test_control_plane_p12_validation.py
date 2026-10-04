"""Fresh validation contracts and faults; no Gemma inference or task scores."""
import base64
import hashlib
import io
import json
import math
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from neumann1.control_plane_v1 import ROUTES, digest, snapshot
from neumann1.control_plane_p1_contract import MODEL, manifest as runtime_manifest
from neumann1.control_plane_p12 import CODE_TOKEN_IDS, PERMUTATIONS, aggregate, plan_cost, score_development
from neumann1.control_plane_p12_validation import (PUBLIC, REFERENCES, TASK_IDS, contract, evaluate_validation,
    opened_development_rows, structural_key, validate_rows, validate_references)
from experiments.control_plane_p12_validation_catalog import catalog
from experiments.control_plane_p12_validation_first import registration, run, ROOT
from experiments.control_plane_p12_validation_replay import replay


def encode(prompt):
    legend = json.loads(prompt.split('\n')[1])['legend']
    p = tuple(next(i for i,x in enumerate(legend) if x['executor']==r) for r in ROUTES)
    return [8,9,PERMUTATIONS.index(p)]


class Backend:
    def __init__(self, winner):
        self.rows = []
        for p in PERMUTATIONS:
            logits = [(8 if p.index(c)==winner else -p.index(c))+[0,20,-10,-30][c] for c in range(4)]
            m = max(logits); normal = m+math.log(sum(math.exp(x-m) for x in logits))
            self.rows.append([x-normal for x in logits])
    def evaluate(self,plan,size,left):
        return {'scores':[self.rows[p[-1]] for p in plan.prefixes],'cost':plan_cost(plan,size),
                'peak_accelerator_memory_bytes':1234}


def fixtures(errors=()):
    rows,refs = catalog(); ledger = {k:0 for k in ('input_rows','score_rows','scored_tokens','evaluated_tokens','padded_tokens','forward_calls')}
    records = []
    for i,(row,ref) in enumerate(zip(rows,refs)):
        # Deliberate synthetic scores, never a real model or validation outcome.
        winner = 0 if i in errors else ROUTES.index(ref['compatible_route'])
        r = score_development(row['view'],encode,CODE_TOKEN_IDS,Backend(winner),ledger,lambda:100000)
        r['task_id'] = row['task_id']; records.append(r)
    return rows,refs,records,ledger


def repin(path):
    report = json.loads((path/'report.json').read_bytes())
    pins = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in path.glob('*.json') if p.name!='terminal.json'}
    (path/'terminal.json').write_text(json.dumps({'files':pins,'decision':report['decision']['verdict'],
        'complete':report['status']=='COMPLETE','no_replacement':True,'development_only':False}))


def archive(path):
    rows,refs,rs,ledger = fixtures()
    values = {'manifest.json':{'registration':registration()[0],'public_rows':rows},
        'core.json':{**MODEL,'device_type':'cuda','device_name':'Tesla T4','evidence_kind':'actual_frozen_model',
                     'framework':'torch-2.11.0+cu128/transformers-5.16.1','torchvision':'0.26.0+cu128'},
        'code_audit.json':{'codes':['A','B','C','D'],'token_ids':list(CODE_TOKEN_IDS),'single_token':True,
                           'special_tokens':False,'tokenizer_sha256':MODEL['tokenizer_sha256']},
        'report.json':{'schema':contract()['schema'],'status':'COMPLETE','generated_calls':0,'tool_calls':0,
            'frontier_calls':0,'new_training':False,'sealed_data_opened':False,
            'ledger':ledger,'core_audit':{'unchanged':True},'accounting_complete':True,
            'controller_wall_ms':100,'whole_study_ms':100,'development_only':False,
            'historical_score_reuse':False,'fresh_validation_opened':True,
            'decision':evaluate_validation(rs,refs,True,True,0,100,100)}}
    values.update({'task_%02d.json'%i:r for i,r in enumerate(rs)})
    for name,data in values.items(): (path/name).write_text(json.dumps(data))
    repin(path)


class FreshValidationContracts(unittest.TestCase):
    def test_catalog_reproduces_frozen_source_and_all_rows_retained(self):
        rows,refs = catalog()
        self.assertEqual(rows,json.loads(PUBLIC.read_bytes())['rows'])
        self.assertEqual(refs,json.loads(REFERENCES.read_bytes())['rows'])
        reg,_ = registration(); self.assertFalse(reg['provenance']['fresh_scores_seen'])
        self.assertEqual(reg['public_sha256'],digest([r['view'] for r in rows]))
        self.assertEqual(reg['dedup']['compared_development_rows'],15)

    def test_original_architecture_bytes_and_geometry_budget_unchanged(self):
        freeze = json.loads((ROOT/'docs/experiments/control_plane_p12_architecture.freeze.json').read_bytes())
        from neumann1.control_plane_p12 import contract as old_contract
        self.assertEqual(freeze['contract'],old_contract())
        self.assertEqual(contract()['criteria'],old_contract()['criteria'])
        self.assertEqual(contract()['budget'],old_contract()['budget'])
        for name,expected in freeze['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected)
        from experiments import control_plane_p12_validation_first as runner
        self.assertIs(runner.score_development,score_development)

    def test_reference_authority_positive_negative_and_corruption(self):
        rows,refs = catalog(); result = validate_references(rows,refs)
        self.assertEqual(result['original_checker_witnesses'],12)
        self.assertEqual(result['negative_controls_rejected'],12)
        refs[0]['private']['exact'] = '0'
        with self.assertRaises(ValueError): validate_references(rows,refs)

    def test_structural_dedup_catches_background_alpha_and_graph_renaming(self):
        old = opened_development_rows()
        for index,old_index in ((0,0),(4,4),(8,8)):
            rows,_ = catalog(); rows[index]['view'] = snapshot(old[old_index]['view'])
            rows[index]['view']['instruction'] = 'Different instruction wording'
            rows[index]['view']['public']['background'] = 'Different background'
            with self.assertRaises(ValueError): validate_rows(rows,old)
        view = snapshot(old[0]['view']); view['public']['expression'] = '(u*v-w)/(x+y)'
        self.assertEqual(structural_key(view),structural_key(old[0]['view']))
        plan = snapshot(old[8]['view']); p = plan['public']; mapping = {n:'v'+n for n in p['domains']}
        p['domains'] = {mapping[k]:v for k,v in p['domains'].items()}
        p['constraints'] = [[op,mapping[a],mapping.get(b,b)] for op,a,b in p['constraints']]
        self.assertEqual(structural_key(plan),structural_key(old[8]['view']))

    def test_no_reference_metadata_in_public_model_rows(self):
        rows,_ = catalog(); self.assertEqual(set(rows[0]['view']),{'instruction','public'})
        rows[0]['family'] = 'math_logic'
        with self.assertRaises(ValueError): validate_rows(rows,opened_development_rows())
        rows,_ = catalog(); rows[0]['view']['public']['hidden_answer'] = '6'
        with self.assertRaises(ValueError): validate_rows(rows,opened_development_rows())

    def test_validation_pass_admits_only_p2_registration(self):
        _,refs,rs,ledger = fixtures()
        d = evaluate_validation(rs,refs,True,True,0,100,100)
        self.assertEqual(d['verdict'],'PASS'); self.assertTrue(d['p2_registration_admitted'])
        self.assertFalse(d['p2_admitted']); self.assertFalse(d['decision3_admitted'])
        self.assertEqual(ledger['forward_calls'],432); self.assertEqual(d['compatible_routes'],12)
        self.assertFalse(evaluate_validation(rs[:11],refs,True,True,0,100,100)['p2_registration_admitted'])

    def test_stable_wrong_routes_fail_semantic_gate_and_per_domain_floor(self):
        _,refs,rs,_ = fixtures(errors=(0,1))
        d = evaluate_validation(rs,refs,True,True,0,100,100)
        self.assertEqual(d['reason'],'TYPED_ROUTE_COMPATIBILITY_FAILURE')
        self.assertEqual(d['compatible_routes'],10); self.assertEqual(d['compatible_by_domain']['math_logic'],2)
        self.assertFalse(d['p2_registration_admitted'])
        _,refs,rs,_ = fixtures(errors=(0,4))
        self.assertEqual(evaluate_validation(rs,refs,True,True,0,100,100)['verdict'],'PASS')

    def test_geometry_generation_identity_and_wall_remain_required(self):
        _,refs,rs,_ = fixtures(); rs[0]['numeric_delta_nats'] = .051
        d = evaluate_validation(rs,refs,True,True,0,100,100)
        self.assertEqual(d['reason'],'NUMERICAL_OR_ORDER_INSTABILITY'); self.assertEqual(d['compatible_routes'],12)
        self.assertEqual(evaluate_validation(rs,refs,True,True,1,100,100)['reason'],'GENERATION_FORBIDDEN')
        self.assertEqual(evaluate_validation(rs,refs,False,True,0,100,100)['verdict'],'NOT_EVALUATED')
        self.assertEqual(evaluate_validation(rs,refs,True,True,0,540001,600000)['reason'],'COMPLETE_COST_WALL_CAP')

    def test_replay_recomputes_raw_scores_costs_admission_and_manifest(self):
        for mutation in (None,'summary','cost','admission','manifest','matrix','frontier'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp); archive(path)
                if mutation:
                    file = path/('task_00.json' if mutation in ('summary','matrix') else 'manifest.json' if mutation=='manifest' else 'report.json')
                    v = json.loads(file.read_bytes())
                    if mutation=='summary': v['summary']['margin_nats'] += 1
                    elif mutation=='matrix': v['passes'][0]['matrix'][0][0] = float('nan')
                    elif mutation=='cost': v['ledger']['forward_calls'] += 1
                    elif mutation=='admission': v['decision']['decision3_admitted'] = True
                    elif mutation=='frontier': v['frontier_calls'] = 1
                    else: v['registration']['provenance']['fresh_scores_seen'] = True
                    file.write_text(json.dumps(v)); repin(path)
                    with self.assertRaises(ValueError): replay(path)
                else:
                    d = replay(path); self.assertTrue(d['integrity_valid']); self.assertTrue(d['p2_registration_admitted'])

    def test_startup_failure_retained_and_incomplete_cannot_admit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'first'
            def fail(): raise RuntimeError('synthetic startup fault; no model')
            with patch('experiments.control_plane_p12_validation_first.subprocess.check_output',return_value='f'*40),\
                 patch('experiments.control_plane_p12_validation_first.subprocess.run'),\
                 patch('experiments.control_plane_p12_validation_first.version',side_effect=lambda p:runtime_manifest()['runtime'][p]),\
                 patch.dict('sys.modules',{'experiments.general_multiplier_accelerator_core':SimpleNamespace(FrozenAcceleratorCore=fail)}):
                d = run(path,'f'*40)
            self.assertEqual(d['status'],'INCOMPLETE'); self.assertFalse(replay(path)['complete'])
            with self.assertRaises(FileExistsError): run(path,'f'*40)
            report = json.loads((path/'report.json').read_bytes()); report['decision']['p2_registration_admitted'] = True
            (path/'report.json').write_text(json.dumps(report)); repin(path)
            with self.assertRaises(ValueError): replay(path)

    def test_original_p12_development_zip_bytes_and_pass_retained(self):
        raw = base64.b64decode((ROOT/'docs/experiments/results/control_plane_p12_first.zip.b64').read_bytes(),validate=True)
        self.assertEqual(len(raw),83071)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'b27748d76b8abdba24ab11ad85f25eb4012c8c9593a12a83590bfbf8666c98ba')
        with zipfile.ZipFile(io.BytesIO(raw)) as z,tempfile.TemporaryDirectory() as tmp:
            pins = json.loads(z.read('archive_manifest.json'))['members']
            self.assertEqual(len(z.namelist()),36); self.assertEqual(set(z.namelist()),set(pins)|{'archive_manifest.json'})
            for n in z.namelist():
                b = z.read(n)
                if n in pins: self.assertEqual(hashlib.sha256(b).hexdigest(),pins[n]['sha256'])
                p = Path(tmp)/n; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b)
            from experiments.control_plane_p12_replay import replay as development_replay
            d = development_replay(Path(tmp)/'neumann_p12_first'); self.assertTrue(d['integrity_valid'])
            self.assertEqual(d['decision']['verdict'],'PASS'); self.assertFalse(d['p2_admitted'])
