"""Model-free P1.1 retained development cost and decision replay."""
import argparse
import hashlib
import json
from pathlib import Path

from neumann1.control_plane_v1 import digest, finite
from neumann1.control_plane_p1_contract import TASK_IDS, PUBLIC_SHA256, validate_identity
from neumann1.control_plane_p11 import Budget, CODES, CodePlan, aggregate, contract, evaluate_development, plan_cost


def replay(directory):
    directory=Path(directory);load=lambda n:json.loads((directory/n).read_bytes())
    terminal=load('terminal.json');files={p.name for p in directory.glob('*.json') if p.name!='terminal.json'}
    if set(terminal['files'])!=files or 'report.json' not in files:raise ValueError('receipt coverage drift')
    for name,expected in terminal['files'].items():
        if Path(name).name!=name or hashlib.sha256((directory/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('first receipt byte drift: '+name)
    report=load('report.json')
    if terminal.get('no_replacement') is not True or report['generated_calls']!=0 or report['tool_calls']!=0:
        raise ValueError('no-generation/no-tool boundary drift')
    if terminal['decision']!=report['decision']['verdict'] or terminal['complete']!=(report['status']=='COMPLETE'):
        raise ValueError('terminal decision drift')
    if report['status']!='COMPLETE':return {'integrity_valid':True,'complete':False,'decision':report['decision'],'model_inference':False}
    manifest=load('manifest.json');rows=manifest['public_rows']
    if manifest['registration']['contract']!=contract() or tuple(r['task_id'] for r in rows)!=TASK_IDS or digest(
            [r['view'] for r in rows])!=PUBLIC_SHA256:raise ValueError('development registration/input drift')
    validate_identity(load('core.json'))
    code=load('code_audit.json');ids=tuple(code['token_ids'])
    if code['codes']!=list(CODES) or code['single_token'] is not True or code['special_tokens'] is not False or len(set(ids))!=4:
        raise ValueError('code-token audit drift')
    if code['tokenizer_sha256']!=contract()['model']['tokenizer_sha256']:raise ValueError('vocabulary identity drift')
    totals={k:0 for k in report['ledger']};records=[]
    for i,row in enumerate(rows):
        record=load('task_%02d.json'%i);records.append(record);passes=record['passes']
        if record['task_id']!=row['task_id'] or record['view_sha256']!=digest(row['view']) or record['trace_sha256']!=digest(passes):
            raise ValueError('development trace identity drift')
        if [p['mode'] for p in passes]!=['batch4','unbatched1','reverse_batch4']:raise ValueError('three modes required')
        for p in passes:
            order=list(reversed(range(8))) if p['mode']=='reverse_batch4' else list(range(8))
            size=1 if p['mode']=='unbatched1' else 4
            if p['status']!='COMPLETE' or p['order']!=order or p['batch_size']!=size or p['code_ids']!=list(ids):
                raise ValueError('registered layout drift')
            if len(p['prefixes'])!=8:raise ValueError('exact eight prefix rows required')
            costs=plan_cost(CodePlan(tuple(tuple(r) for r in p['prefixes']),ids),size)
            if costs!=p['planned'] or costs!=p['actual']:raise ValueError('exact prefix/forward accounting drift')
            for k,v in costs.items():totals[k]+=v
            aggregate(p['matrix'])
        primary=aggregate(passes[0]['matrix'])
        delta=max(abs(passes[0]['matrix'][r][c]-p['matrix'][r][c]) for p in passes[1:] for r in range(8) for c in range(4))
        if record['summary']!=primary or record['numeric_delta_nats']!=delta:raise ValueError('route summary/numeric drift')
        finite(record['complete_ms'],True)
    if totals!=report['ledger'] or any(v>getattr(Budget(),k) for k,v in totals.items()):raise ValueError('complete aggregate budget drift')
    verdict=evaluate_development(records,report['core_audit'].get('unchanged'),report['accounting_complete'],
                                 report['generated_calls'],report['controller_wall_ms'],report['whole_study_ms'])
    if verdict!=report['decision']:raise ValueError('development gate drift')
    return {'integrity_valid':True,'complete':True,'decision':verdict,'ledger':totals,'model_inference':False,
            'p2_admitted':False,'decision3_admitted':False,'development_only':True}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--directory',required=True);args=parser.parse_args()
    print(json.dumps(replay(args.directory),sort_keys=True))
