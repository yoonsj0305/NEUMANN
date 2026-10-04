"""Independent model-free fresh-validation accounting, robustness and first-receipt replay."""
import argparse
import hashlib
import json
from pathlib import Path

from neumann1.control_plane_v1 import digest, finite
from neumann1.control_plane_p1_contract import validate_identity
from neumann1.control_plane_p12 import Budget, CODE_TOKEN_IDS, CODES, CodePlan, aggregate, plan_cost


from neumann1.control_plane_p12_validation import TASK_IDS, REFERENCES, contract, evaluate_validation, validate_rows, opened_development_rows
from experiments.control_plane_p12_validation_first import registration

def replay(directory):
    directory = Path(directory); load = lambda n: json.loads((directory/n).read_bytes())
    terminal = load('terminal.json'); files = {p.name for p in directory.glob('*.json') if p.name != 'terminal.json'}
    if set(terminal['files']) != files or 'report.json' not in files: raise ValueError('receipt coverage drift')
    for name, expected in terminal['files'].items():
        if Path(name).name != name or hashlib.sha256((directory/name).read_bytes()).hexdigest() != expected:
            raise ValueError('first receipt byte drift: '+name)
    report = load('report.json')
    if terminal.get('no_replacement') is not True or report['generated_calls'] != 0 or report['tool_calls'] != 0:
        raise ValueError('no-generation/no-tool boundary drift')
    if report.get('frontier_calls') != 0 or report.get('new_training') is not False or report.get('sealed_data_opened') is not False:
        raise ValueError('no-frontier/no-training/no-sealed boundary drift')
    if report.get('schema') != contract()['schema'] or report.get('development_only') is not False:
        raise ValueError('registered fresh-validation schema required')
    if report.get('historical_score_reuse') is not False or report.get('fresh_validation_opened') is not True:
        raise ValueError('fresh validation only; no historical inference reuse')
    if terminal['decision'] != report['decision']['verdict'] or terminal['complete'] != (report['status'] == 'COMPLETE'):
        raise ValueError('terminal decision drift')
    for key in ('p2_admitted','decision3_admitted'):
        if report['decision'].get(key) is not False: raise ValueError('development admission drift')
    if report['decision'].get('fresh_validation_registered') is not True: raise ValueError('registered validation required')
    if report['status'] != 'COMPLETE':
        if report['decision'].get('p2_registration_admitted') is not False or report['decision']['verdict']=='PASS':
            raise ValueError('incomplete validation cannot admit registration')
        return {'integrity_valid':True,'complete':False,'decision':report['decision'],'model_inference':False}
    manifest = load('manifest.json'); rows = manifest['public_rows']; reg, original_rows = registration()
    if manifest['registration'] != reg or rows != original_rows: raise ValueError('frozen validation manifest drift')
    validate_rows(rows,opened_development_rows())
    if manifest['registration']['contract'] != contract() or tuple(r['task_id'] for r in rows) != TASK_IDS or digest(
            [r['view'] for r in rows]) != reg['public_sha256']: raise ValueError('development registration/input drift')
    validate_identity(load('core.json'))
    code = load('code_audit.json'); ids = tuple(code['token_ids'])
    if code['codes'] != list(CODES) or code['single_token'] is not True or code['special_tokens'] is not False or ids != CODE_TOKEN_IDS:
        raise ValueError('code-token audit drift')
    if code['tokenizer_sha256'] != contract()['architecture']['model']['tokenizer_sha256']: raise ValueError('vocabulary identity drift')
    totals = {k:0 for k in report['ledger']}; records = []
    for i, row in enumerate(rows):
        record = load('task_%02d.json'%i); records.append(record); passes = record['passes']
        if record['task_id'] != row['task_id'] or record['view_sha256'] != digest(row['view']) or record['trace_sha256'] != digest(passes):
            raise ValueError('development trace identity drift')
        if [p['mode'] for p in passes] != ['batch4','unbatched1','reverse_batch4']: raise ValueError('three modes required')
        for p in passes:
            order = list(reversed(range(24))) if p['mode'] == 'reverse_batch4' else list(range(24))
            size = 1 if p['mode'] == 'unbatched1' else 4
            if p['status'] != 'COMPLETE' or p['order'] != order or p['batch_size'] != size or p['code_ids'] != list(ids):
                raise ValueError('registered full-S4 layout drift')
            if len(p['prefixes']) != 24: raise ValueError('exactly 24 prefixes required')
            if type(p.get('peak_accelerator_memory_bytes')) is not int or p['peak_accelerator_memory_bytes'] <= 0:
                raise ValueError('positive actual peak VRAM receipt required')
            costs = plan_cost(CodePlan(tuple(tuple(r) for r in p['prefixes']),ids),size)
            if costs != p['planned'] or costs != p['actual']: raise ValueError('exact prefix/forward accounting drift')
            for k, v in costs.items(): totals[k] += v
            aggregate(p['matrix'])
        summary = aggregate(passes[0]['matrix'])
        delta = max(abs(passes[0]['matrix'][r][c]-p['matrix'][r][c]) for p in passes[1:] for r in range(24) for c in range(4))
        if record['summary'] != summary or record['numeric_delta_nats'] != delta: raise ValueError('full mean/robustness/numeric drift')
        finite(record['complete_ms'],True)
    if totals != report['ledger'] or any(v > getattr(Budget(),k) for k,v in totals.items()): raise ValueError('complete aggregate budget drift')
    verdict = evaluate_validation(records,json.loads(REFERENCES.read_bytes())['rows'],report['core_audit'].get('unchanged'),report['accounting_complete'],
                                   report['generated_calls'],report['controller_wall_ms'],report['whole_study_ms'])
    if verdict != report['decision']: raise ValueError('development gate drift')
    return {'integrity_valid':True,'complete':True,'decision':verdict,'ledger':totals,'model_inference':False,
            'p2_admitted':False,'decision3_admitted':False,'development_only':False,'p2_registration_admitted':verdict['p2_registration_admitted']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--directory',required=True); args = parser.parse_args()
    print(json.dumps(replay(args.directory),sort_keys=True))
