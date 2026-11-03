"""P0.9: infer causal radius, boundary and local operator semantics jointly.

Purely classical, finitely bounded structural hypothesis search.  Never
presented as neural PRH/JEPA learning or proof of a new instruction set.
First-only preregistration: docs/research/prh_q3_structure_discovery_p09_prereg_2026_11_03.md
"""
from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import argparse
import json
import platform
import time

import numpy as np

SCHEMA = 'neumann.prh.local-structure-discovery.p09.v1'
CONTRACT = {
    'schema': SCHEMA,
    'base_seed': 20261109,
    'cases': [[0,'none',4], [1,'periodic',4], [1,'zero-pad',4],
              [2,'periodic',4], [2,'zero-pad',4]],
    'train_lengths': [89,97,113,131,149],
    'test_1d_lengths': [173,211],
    'test_2d_shapes': [[3,181],[5,199]],
    'allowed_radius': [0,1,2],
    'allowed_boundary': ['none', 'periodic', 'zero-pad'],
    'source_rule_condition': 'outermost_left_and_right_bits_essential_for_radius_gt_0',
    'rule_sampling_seed': 'base_seed+task_index*101',
    'train_sampling_seed': 'base_seed+task_index*101+11',
    'test_sampling_seed': 'base_seed+task_index*101+911',
    'no_resampling_on_results': True,
    'gate': {'complete_independent_correct':20, 'one_d_exact':40,
             'two_d_exact':40, 'negative_rejections':7},
    'negative_controls': ['undercoverage','contradiction','shape','alphabet',
                          'radius3_nonlocal','bool_radius_ast','invalid_boundary_ast'],
    'jepa': 'NOT_RUN',
    'global_q1_to_q7': 'OPEN',
}


class Reject(ValueError):
    pass


@dataclass(frozen=True)
class LocalOperator:
    radius: int
    boundary: str
    table: tuple[int, ...]
    kind: str = 'LOCAL_CA'

    def __post_init__(self) -> None:
        if type(self.radius) is not int or self.radius not in (0,1,2):
            raise Reject('ABSTAIN_ILLTYPED_RADIUS')
        if type(self.boundary) is not str or self.boundary not in (
            ('none',) if self.radius == 0 else ('periodic','zero-pad')
        ):
            raise Reject('ABSTAIN_ILLTYPED_BOUNDARY')
        size = 1 << (2*self.radius + 1)
        if (type(self.table) is not tuple or len(self.table) != size or
            any(type(v) is not int or v not in (0,1) for v in self.table) or
            self.kind != 'LOCAL_CA'):
            raise Reject('ABSTAIN_ILLTYPED_TRUTH_TABLE')

    def ast(self) -> dict:
        return {'kind':self.kind, 'radius':self.radius,
                'boundary':self.boundary, 'table':list(self.table)}


def load_ast(ast: dict) -> LocalOperator:
    if type(ast) is not dict or set(ast) != {'kind','radius','boundary','table'}:
        raise Reject('ABSTAIN_ILLTYPED_AST')
    if type(ast['table']) is not list:
        raise Reject('ABSTAIN_ILLTYPED_AST')
    return LocalOperator(ast['radius'], ast['boundary'], tuple(ast['table']), ast['kind'])


def input_row(seq) -> list[int]:
    if (type(seq) is not list or len(seq) < 5 or
        any(type(v) is not int or v not in (0,1) for v in seq)):
        raise Reject('ABSTAIN_BAD_INPUT_ALPHABET_OR_LENGTH')
    return seq


def context(seq: list[int], index: int, radius: int, boundary: str) -> int:
    """Learner context extraction, not the reference implementation."""
    n = len(seq)
    key = 0
    for off in range(-radius, radius+1):
        pos = index + off
        if boundary == 'periodic':
            val = seq[pos % n]
        elif boundary in ('none','zero-pad'):
            val = seq[pos] if 0 <= pos < n else 0
        else:
            raise Reject('ABSTAIN_UNKNOWN_BOUNDARY')
        key = (key << 1) | val
    return key


def fit_candidate(train: list[dict], radius: int, boundary: str) -> tuple[LocalOperator | None, dict]:
    values: list[int | None] = [None] * (1 << (2*radius+1))
    counts = [0] * len(values)
    observations = 0
    for pair in train:
        x,y = pair['input'], pair['output']
        for i in range(len(x)):
            k = context(x,i,radius,boundary)
            counts[k] += 1
            observations += 1
            if values[k] is None:
                values[k] = y[i]
            elif values[k] != y[i]:
                return None, {'reason':'CONTRADICTION', 'observations':observations,
                              'covered':sum(v is not None for v in values)}
    if any(v is None for v in values):
        return None, {'reason':'INCOMPLETE', 'observations':observations,
                      'covered':sum(v is not None for v in values)}
    compiled = LocalOperator(radius,boundary,tuple(values))
    if any(execute_1d(compiled, ex['input']) != ex['output'] for ex in train):
        return None, {'reason':'REPLAY_MISMATCH', 'observations':observations}
    return compiled, {'reason':'SUCCESS', 'observations':observations,
                      'covered':len(values)}


def execute_1d(op: LocalOperator, src: list[int]) -> list[int]:
    """Independent vectorized compilation; no dynamic eval/exec allowed."""
    row = input_row(src)
    x = np.asarray(row,dtype=np.int64)
    n = len(x)
    key = np.zeros(n,dtype=np.int64)
    for off in range(-op.radius, op.radius+1):
        if op.boundary == 'periodic':
            shifted = np.roll(x, -off)
        else:
            shifted = np.zeros(n,dtype=np.int64)
            if off < 0:
                shifted[-off:] = x[:n+off]
            elif off > 0:
                shifted[:n-off] = x[off:]
            else:
                shifted = x
        key = key*2 + shifted
    return np.asarray(op.table,dtype=np.int64)[key].tolist()


def execute_2d(op: LocalOperator, src: list[list[int]]) -> list[list[int]]:
    if (type(src) is not list or not src or
        any(type(row) is not list or len(row) != len(src[0]) for row in src)):
        raise Reject('ABSTAIN_RAGGED_MATRIX')
    return [execute_1d(op,row) for row in src]


def reference_1d(row: list[int], radius: int, boundary: str, bits: list[int]) -> list[int]:
    """Separate loop-based oracle, scorer/source ONLY, never passed to infer."""
    n = len(row)
    out = []
    for pos in range(n):
        value = 0
        for i in range(2*radius+1):
            j = pos-radius+i
            if boundary == 'periodic':
                bit = row[j % n]
            else:
                bit = row[j] if (j>=0 and j<n) else 0
            value = value*2 + bit
        out.append(bits[value])
    return out


def reference_2d(rows: list[list[int]], r: int, b: str, bits: list[int]):
    return [reference_1d(row,r,b,bits) for row in rows]


def infer(train: list[dict], *, fixed_radius: int | None = None,
          fixed_boundary: str | None = None) -> dict:
    """Choose shortest uniquely supported local semantics. No task metadata."""
    t0 = time.perf_counter_ns()
    if type(train) is not list or not train:
        return {'status':'ABSTAIN_NO_TRAIN', 'ast':None, 'elapsed_ns':time.perf_counter_ns()-t0}
    try:
        for ex in train:
            if type(ex) is not dict or set(ex) != {'input','output'}:
                raise Reject('ABSTAIN_BAD_EXAMPLE_SCHEMA')
            x = input_row(ex['input'])
            y = ex['output']
            if type(y) is not list or len(x) != len(y) or any(type(v) is not int or v not in (0,1) for v in y):
                raise Reject('ABSTAIN_BAD_OUTPUT_SHAPE_OR_ALPHABET')
    except Reject as exc:
        return {'status':str(exc),'ast':None,'elapsed_ns':time.perf_counter_ns()-t0}
    tried = []
    for r in CONTRACT['allowed_radius']:
        if fixed_radius is not None and r != fixed_radius:
            continue
        boundaries = ['none'] if r == 0 else ['periodic','zero-pad']
        if fixed_boundary is not None:
            boundaries = [b for b in boundaries if b==fixed_boundary]
        matches = []
        for b in boundaries:
            candidate,stats = fit_candidate(train, r, b)
            tried.append({'radius':r,'boundary':b,**stats})
            if candidate is not None:
                matches.append(candidate)
        if len(matches) > 1:
            return {'status':'ABSTAIN_AMBIGUOUS_BOUNDARY','ast':None,
                    'trials':tried,'elapsed_ns':time.perf_counter_ns()-t0}
        if len(matches) == 1:
            candidate = matches[0]
            return {'status':'INFERRED_UNIQUE_LOCAL_STRUCTURE','ast':candidate.ast(),
                    'trials':tried,'elapsed_ns':time.perf_counter_ns()-t0}
    return {'status':'ABSTAIN_NO_UNIQUE_LOCAL_STRUCTURE','ast':None,
            'trials':tried,'elapsed_ns':time.perf_counter_ns()-t0}


def rule_outer_bits_essential(table: list[int], r: int) -> bool:
    if r == 0:
        return True
    size = 2*r+1
    top_bit,low_bit = 1<<(size-1), 1
    return (any(table[k] != table[k^top_bit] for k in range(len(table))) and
            any(table[k] != table[k^low_bit] for k in range(len(table))))


def source_tasks():
    """Per-task independent generation, no selection conditioned on results."""
    index = 0
    for r,b,count in CONTRACT['cases']:
        for _ in range(count):
            seed = CONTRACT['base_seed']+index*101
            rng = np.random.default_rng(seed)
            table_len = 1 << (2*r+1)
            attempts = 0
            while True:
                table = rng.integers(0,2,size=table_len).astype(int).tolist()
                attempts += 1
                if rule_outer_bits_essential(table,r):
                    break
            train_rng = np.random.default_rng(seed+11)
            test_rng = np.random.default_rng(seed+911)
            def row(rng,length):
                return rng.integers(0,2,size=length).astype(int).tolist()
            train = []
            for length in CONTRACT['train_lengths']:
                seq = row(train_rng,length)
                train.append({'input':seq,'output':reference_1d(seq,r,b,table)})
            tests_1d = []
            for length in CONTRACT['test_1d_lengths']:
                seq = row(test_rng,length)
                tests_1d.append({'input':seq,'output':reference_1d(seq,r,b,table)})
            tests_2d = []
            for height,width in CONTRACT['test_2d_shapes']:
                seqs = [row(test_rng,width) for j in range(height)]
                tests_2d.append({'input':seqs,'output':reference_2d(seqs,r,b,table)})
            yield {'index':index,'reference_radius':r,'reference_boundary':b,
                   'reference_table':table,'rule_draw_attempts':attempts,
                   'train':train,'test_1d':tests_1d,'test_2d':tests_2d}
            index += 1


def negative_controls(first_task):
    source = first_task['train']
    missing = [{'input':[0]*n,'output':[0]*n} for n in CONTRACT['train_lengths']]
    wrong = deepcopy(source);wrong[0]['output'][0] ^= 1
    shape = deepcopy(source);shape[0]['output'].pop()
    alphabet = deepcopy(source);alphabet[0]['input'][0] = 2
    r3_rng = np.random.default_rng(CONTRACT['base_seed']+777)
    nonlocal_examples=[]
    for n in CONTRACT['train_lengths']:
        row = r3_rng.integers(0,2,size=n).astype(int).tolist()
        nonlocal_examples.append({'input':row, 'output':[row[(i-3)%n] for i in range(n)]})
    ast = {'kind':'LOCAL_CA','radius':True,'boundary':'none','table':[0,1]}
    strict_bool_reject = False
    try:
        load_ast(ast)
    except Reject:
        strict_bool_reject = True
    ast={'kind':'LOCAL_CA','radius':1,'boundary':'reflect','table':[0]*8}
    invalid_boundary_reject=False
    try:
        load_ast(ast)
    except Reject:
        invalid_boundary_reject=True
    return {
        'undercoverage':infer(missing)['status'],
        'contradiction':infer(wrong)['status'],
        'shape':infer(shape)['status'],
        'alphabet':infer(alphabet)['status'],
        'radius3_nonlocal':infer(nonlocal_examples)['status'],
        'bool_radius_ast': 'ABSTAIN_ILLTYPED_RADIUS' if strict_bool_reject else 'UNSAFE_ACCEPT',
        'invalid_boundary_ast':'ABSTAIN_ILLTYPED_BOUNDARY' if invalid_boundary_reject else 'UNSAFE_ACCEPT',
    }


def evaluate_case(case):
    t0=time.perf_counter_ns()
    result=infer(case['train'])
    t1=time.perf_counter_ns()
    restricted=infer(case['train'],fixed_radius=1,fixed_boundary='periodic')
    t2=time.perf_counter_ns()
    if result['ast'] is not None:
        op=load_ast(result['ast'])
        original_verified = all(execute_1d(op,p['input'])==p['output'] for p in case['train'])
        local_verified = op.radius==case['reference_radius'] and op.boundary==case['reference_boundary'] and list(op.table)==case['reference_table']
        complete_certificate = sum(a==b for a,b in zip(op.table,case['reference_table'])) if op.radius==case['reference_radius'] else 0
        exact_1d=[execute_1d(op,t['input'])==t['output'] for t in case['test_1d']]
        exact_2d=[execute_2d(op,t['input'])==t['output'] for t in case['test_2d']]
    else:
        original_verified=False;local_verified=False;complete_certificate=0
        exact_1d=[False]*len(case['test_1d'])
        exact_2d=[False]*len(case['test_2d'])
    t3=time.perf_counter_ns()
    if restricted['ast'] is not None:
        restricted_op=load_ast(restricted['ast'])
        restricted_exact=all(execute_1d(restricted_op,t['input'])==t['output'] for t in case['test_1d']) and all(execute_2d(restricted_op,t['input'])==t['output'] for t in case['test_2d'])
    else:
        restricted_exact=False
    t4=time.perf_counter_ns()
    return {'task_index':case['index'],'reference_radius_for_scorer_only':case['reference_radius'],
            'reference_boundary_for_scorer_only':case['reference_boundary'],
            'reference_table_sha256_for_scorer_only':sha256(json.dumps(case['reference_table']).encode()).hexdigest(),
            'source_rule_sampling_attempts':case['rule_draw_attempts'],
            'training_pairs_sha256':sha256(json.dumps(case['train'],sort_keys=True).encode()).hexdigest(),
            'induction':result,'independent_original_train_verified':original_verified,
            'independent_complete_structure_verified':local_verified,
            'local_table_certificate_correct_entries':complete_certificate,
            'table_entries_total':len(case['reference_table']),
            'heldout_1d_exact':exact_1d,'heldout_2d_exact':exact_2d,
            'restricted_fixed_radius1_periodic_train_status':restricted['status'],
            'restricted_fixed_radius1_periodic_heldout_all_correct':restricted_exact,
            'full_induction_plus_original_verify_and_test_ns':(t1-t0)+(t3-t2),
            'restricted_induction_plus_test_ns':(t2-t1)+(t4-t3)}


def run():
    start=time.perf_counter_ns()
    cases=list(source_tasks())
    rows=[evaluate_case(case) for case in cases]
    negatives=negative_controls(cases[0])
    rejected={k:v.startswith('ABSTAIN_') for k,v in negatives.items()}
    metrics={
        'exact_structure_and_table':sum(r['independent_complete_structure_verified'] for r in rows),
        'complete_original_train_certificates':sum(r['independent_original_train_verified'] and r['local_table_certificate_correct_entries']==r['table_entries_total'] for r in rows),
        'heldout_1d_exact':sum(sum(r['heldout_1d_exact']) for r in rows),
        'heldout_2d_exact':sum(sum(r['heldout_2d_exact']) for r in rows),
        'negative_controls_rejected':sum(rejected.values()),
        'restricted_fixed_radius1_periodic_solved':sum(r['restricted_fixed_radius1_periodic_heldout_all_correct'] for r in rows),
        'full_induction_plus_verify_test_ns':sum(r['full_induction_plus_original_verify_and_test_ns'] for r in rows),
        'restricted_baseline_ns_not_iso_capability':sum(r['restricted_induction_plus_test_ns'] for r in rows),
        'trials_total':sum(len(r['induction'].get('trials',[])) for r in rows),
        'examinations_of_training_cells':sum(sum(t['observations'] for t in r['induction'].get('trials',[])) for r in rows),
    }
    g=CONTRACT['gate']
    passed=metrics['exact_structure_and_table']==g['complete_independent_correct'] and metrics['complete_original_train_certificates']==g['complete_independent_correct'] and metrics['heldout_1d_exact']==g['one_d_exact'] and metrics['heldout_2d_exact']==g['two_d_exact'] and metrics['negative_controls_rejected']==g['negative_rejections']
    return {'contract':CONTRACT,
            'first_local_gate':'P09_BOUNDED_SCOPE_DISCOVERY_PASS' if passed else 'P09_BOUNDED_SCOPE_DISCOVERY_FAIL',
            'metrics':metrics,'rows':rows,'negative_controls':negatives,'negative_rejections':rejected,
            'total_study_cpu_wall_ns_including_source_generation':time.perf_counter_ns()-start,
            'global_Q1_to_Q7':'OPEN','JEPA':'NOT_RUN','frontier_gap':'NOT_RUN',
            'open_ended_grammar_invention':'NOT_DEMONSTRATED',
            'strong_classical_match':'EXACT_ADAPTIVE_SEARCH_IS_ITSELF_CLASSICAL_DIRECT',
            'energy_joule':None,'flops':None,'peak_ram_bytes':None,'monetary_cost_usd':None,
            'environment':{'python':platform.python_version(),'numpy':np.__version__, 'machine':platform.machine()}}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args()
    result=run()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x',encoding='utf8') as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({'verdict':result['first_local_gate'],'metrics':result['metrics'],
                      'negatives':result['negative_controls']},indent=2,sort_keys=True))


if __name__=='__main__':
    main()
