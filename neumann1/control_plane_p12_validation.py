"""Frozen P1.2 on new authored opened tasks; permits P2 registration only."""
from dataclasses import asdict
from pathlib import Path
import ast
import itertools
import json
import math
import re

from neumann1.control_plane_v1 import ROUTES, canonical, digest, finite, public_view
from neumann1.control_plane_p12 import Budget, CRITERIA, contract as architecture_contract

SCHEMA = 'neumann.control-plane-p12-fresh-validation.v1'
TASK_IDS = tuple('p12v_%02d' % i for i in range(1,13))
REFERENCE_GATE = {'minimum_compatible_routes':10, 'minimum_per_domain':3,
                  'interpretation':'registered typed executor compatibility, not cheapest executor or solved answers'}
ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT/'docs/experiments/control_plane_p12_validation_public.json'
REFERENCES = ROOT/'docs/experiments/control_plane_p12_validation_references.json'
OLD_PUBLIC = ROOT/'docs/experiments/control_plane_p1_opened_public.json'


def structural_key(view):
    p = public_view(view)['public']
    if 'expression' in p:
        tree = ast.parse(p['expression'],mode='eval'); names = {}
        for n in ast.walk(tree):
            if isinstance(n,ast.Name): n.id = names.setdefault(n.id,'v%d'%len(names))
        return 'arithmetic:'+ast.dump(tree,include_attributes=False)
    if 'requirement' in p:
        return 'coding:'+re.sub(r'[^a-z0-9]+',' ',p['requirement'].lower()).strip()
    names = sorted(p['domains']); variants = []
    for order in itertools.permutations(names):
        ids = {n:i for i,n in enumerate(order)}; edges = []
        for op,a,b in p['constraints']:
            left = 'v%d'%ids[a]; right = 'v%d'%ids[b] if type(b) is str else 'constant'
            if op in ('eq','ne'): left,right = sorted((left,right))
            edges.append((op,left,right))
        variants.append(canonical({'sizes':[len(p['domains'][n]) for n in order],'edges':sorted(edges)}))
    return 'csp:'+min(variants)


def validate_rows(rows, old_rows):
    if tuple(r.get('task_id') for r in rows) != TASK_IDS: raise ValueError('exact ordered fresh coverage required')
    if any(set(r)!={'task_id','view'} for r in rows): raise ValueError('no reference metadata in model rows')
    views = [public_view(r['view']) for r in rows]; old = [public_view(r['view']) for r in old_rows]
    for view in views:
        p = view['public']
        fields = ({'expression','bindings','background'} if 'expression' in p else
                  {'requirement','examples','background'} if 'requirement' in p else
                  {'domains','constraints','background'})
        if set(p) != fields: raise ValueError('exact typed public fields; no reference metadata')
    keys = [structural_key(v) for v in views]
    if len(set(keys)) != 12 or set(keys)&{structural_key(v) for v in old}: raise ValueError('structural duplicate')
    relevant = lambda v:digest({k:x for k,x in v['public'].items() if k!='background'})
    if set(map(relevant,views))&set(map(relevant,old)): raise ValueError('content duplicate')
    return {'exact_and_relevant_duplicates':0,'structural_duplicates':0,'compared_development_rows':len(old),
            'fresh_rows':12,'method':'arithmetic alpha-AST; normalized coding specification; CSP graph isomorphism with domain cardinalities/constant markers',
            'limits':'coding semantic equivalence and domain-wide novelty are not proved'}


def opened_development_rows():
    from neumann1.general_runtime_v106 import development_tasks
    rows = json.loads(OLD_PUBLIC.read_bytes())['rows']
    return rows + [{'task_id':t['id'],'view':{'instruction':t['instruction'],'public':t['public']}}
                   for t, _ in development_tasks()]


def validate_references(rows, references):
    from neumann1.general_runtime_v106 import _rational, verify_original
    if tuple(r['task_id'] for r in references) != TASK_IDS: raise ValueError('reference coverage drift')
    counts = {}; routes = {'math_logic':'ARITHMETIC','coding':'PYTHON','constraint_planning':'CSP'}
    for row, ref in zip(rows,references):
        if ref['compatible_route'] != routes[ref['family']]: raise ValueError('typed compatibility reference drift')
        task = {'id':row['task_id'],'family':ref['family'],**row['view']}; private = ref['private']; witness = ref['witness']
        if not verify_original(task,witness,private,2000): raise ValueError('original checker rejected construction witness')
        if ref['family']=='math_logic':
            if _rational(task['public']['expression'],task['public']['bindings']) != private['exact']:
                raise ValueError('literal rational reference disagrees with supplied expression')
            bad = '987654321'
        elif ref['family']=='coding': bad = 'def solve(items):\n    return None\n'
        else: bad = {k:987654321 for k in task['public']['domains']}
        if verify_original(task,bad,private,2000): raise ValueError('checker negative control accepted')
        counts[ref['family']] = counts.get(ref['family'],0)+1
    if counts != {'math_logic':4,'coding':4,'constraint_planning':4}: raise ValueError('registered 4/4/4 composition required')
    return {'original_checker_witnesses':12,'negative_controls_rejected':12,'coding_scope':'finite original-spec tests only',
            'model_inference':False}


def contract():
    return {'schema':SCHEMA,'architecture_origin_head':'75d9843e0d893e1a34394258b14c984d461cec1c',
            'architecture':architecture_contract(), 'task_ids':list(TASK_IDS), 'criteria':dict(CRITERIA),
            'reference_gate':dict(REFERENCE_GATE),'budget':asdict(Budget()),'task_count':12,
            'scope':'new authored opened problems within the three existing typed interfaces; no external benchmark, open-set or scaling claim',
            'first_only':True,'validation_scores_seen_at_registration':False,'generation_allowed':False,'tool_calls':0,
            'frontier_calls':0,'new_training':False,'sealed_data_opened':False,
            'p2_registration_only_on_pass':True,'p2_admitted':False,'decision3_admitted':False}


def evaluate_validation(records, references, unchanged, accounting_complete, generated_calls, controller_ms, study_ms):
    boundary = {'p2_admitted':False,'p2_registration_admitted':False,'decision3_admitted':False,
                'general_capability_gate':'NOT_EVALUATED','global_questions_closed':[],
                'development_only':False,'fresh_validation_registered':True}
    diagnostics = {}
    def result(verdict,reason): return {**boundary,**diagnostics,'verdict':verdict,'reason':reason}
    if generated_calls != 0: return result('FAIL','GENERATION_FORBIDDEN')
    if len(records)!=12 or unchanged is not True or accounting_complete is not True:
        return result('NOT_EVALUATED','INCOMPLETE_OR_IDENTITY_DRIFT')
    if tuple(r['task_id'] for r in records)!=TASK_IDS or tuple(r['task_id'] for r in references)!=TASK_IDS:
        return result('NOT_EVALUATED','FRESH_COVERAGE_DRIFT')
    hits = {}; compatible = 0
    for record,ref in zip(records,references):
        hit = int(record.get('summary',{}).get('winner')==ref['compatible_route'])
        compatible += hit; hits[ref['family']] = hits.get(ref['family'],0)+hit
    diagnostics.update(compatible_routes=compatible,compatible_by_domain=hits)
    if finite(controller_ms,True)>Budget().controller_wall_ms or finite(study_ms,True)>Budget().study_wall_ms:
        return result('FAIL','COMPLETE_COST_WALL_CAP')
    winners = []; centered = []
    for record,ref in zip(records,references):
        if record['status']!='COMPLETE': return result('NOT_EVALUATED','INCOMPLETE')
        if finite(record['complete_ms'],True)>Budget().task_wall_ms: return result('FAIL','TASK_WALL_CAP')
        s = record['summary']
        if finite(record['numeric_delta_nats'],True)>CRITERIA['numeric_tolerance_nats']: return result('FAIL','NUMERICAL_OR_ORDER_INSTABILITY')
        if finite(s['max_centered_loo_delta_nats'],True)>CRITERIA['loo_centered_tolerance_nats']: return result('FAIL','FULL_MEAN_ORBIT_SENSITIVITY')
        if finite(s['margin_nats'],True)<=CRITERIA['minimum_full_margin_nats'] or s['all_loo_winners_stable'] is not True:
            return result('FAIL','AMBIGUOUS_OR_UNSTABLE_FULL_MEAN_WINNER')
        scores = [finite(s['scores'][r]) for r in ROUTES]; mean = math.fsum(scores)/4
        centered.append([v-mean for v in scores]); winners.append(s['winner'])
    spread = max(max(row[k] for row in centered)-min(row[k] for row in centered) for k in range(4))
    if len(set(winners))<CRITERIA['distinct_winners'] or max(winners.count(r) for r in ROUTES)>CRITERIA['dominant_winner_max'] or spread<CRITERIA['centered_task_range_min_nats']:
        return result('FAIL','DEGENERATE_ROUTE_SELECTION')
    okay = compatible>=REFERENCE_GATE['minimum_compatible_routes'] and len(hits)==3 and min(hits.values())>=REFERENCE_GATE['minimum_per_domain']
    return {**result('PASS' if okay else 'FAIL','FRESH_ROUTING_DIAGNOSTIC_ONLY' if okay else 'TYPED_ROUTE_COMPATIBILITY_FAILURE'),
            'p2_registration_admitted':okay,'compatible_routes':compatible,'compatible_by_domain':hits,
            'winner_counts':{r:winners.count(r) for r in ROUTES},'centered_task_range_nats':spread,
            'next':'REGISTER_P2_WITHOUT_EXECUTING_IT' if okay else 'PRESERVE_FIRST_VALIDATION_FAILURE'}
