"""First-only P1.1 opened development. Never fresh validation or P2."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import traceback
from pathlib import Path
from time import perf_counter_ns
from importlib.metadata import version

from neumann1.control_plane_v1 import canonical, digest, snapshot
from neumann1.control_plane_scoring_v1 import attach_frozen_gemma
from neumann1.control_plane_p1_contract import TASK_IDS, PUBLIC_SHA256, manifest as p1_manifest, validate_identity
from neumann1.control_plane_p11 import (Budget, SCHEMA, NextCodeBackend, audit_codes, contract,
                                       evaluate_development, score_development)
from experiments.control_plane_p1_first import forbid_generation, write_new

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'docs/experiments/control_plane_p1_opened_public.json'
REGISTRATION=ROOT/'docs/experiments/control_plane_p11_dev.preregister.json'


def registration():
    data=json.loads(REGISTRATION.read_bytes())
    if data['contract']!=contract():raise ValueError('P1.1 source/contract freeze drift')
    for name,expected in data['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:raise ValueError('source drift: '+name)
    rows=json.loads(PUBLIC.read_bytes())['rows']
    if tuple(r['task_id'] for r in rows)!=TASK_IDS or any(set(r)!={'task_id','view'} for r in rows):
        raise ValueError('exact development-only input coverage required')
    if digest([r['view'] for r in rows])!=PUBLIC_SHA256:raise ValueError('original development input drift')
    return data,rows


def tokenizer_readiness():
    """CI: original vocabulary only, no model weights or task rows loaded."""
    from transformers import AutoTokenizer
    from neumann1.control_plane_p1_contract import MODEL
    tokenizer=AutoTokenizer.from_pretrained(MODEL['model_id'],revision=MODEL['model_revision'],
                                           token=False,trust_remote_code=False)
    return audit_codes(tokenizer)


def run(directory,frozen_head):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    began=perf_counter_ns();controller_start=None;core=None;audit={};counter={'calls':0};records=[];error=None
    elapsed=lambda:(perf_counter_ns()-began)/1e6
    controller_ms=lambda:0. if controller_start is None else (perf_counter_ns()-controller_start)/1e6
    write_new(directory/'study_started.json',{'schema':SCHEMA,'frozen_head':frozen_head,'development_only':True})
    ledger={k:0 for k in ('input_rows','score_rows','scored_tokens','evaluated_tokens','padded_tokens','forward_calls')}
    try:
        reg,rows=registration()
        write_new(directory/'manifest.json',{'registration':reg,'public_rows':rows,'frozen_head':frozen_head})
        if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=frozen_head:
            raise ValueError('exact frozen source commit required')
        subprocess.run(['git','diff','--exit-code','HEAD','--'],cwd=ROOT,check=True,capture_output=True)
        for package,expected in p1_manifest()['runtime'].items():
            if version(package)!=expected:raise ValueError('original runtime mismatch: '+package)
        from experiments.general_multiplier_accelerator_core import FrozenAcceleratorCore
        core=FrozenAcceleratorCore();validate_identity(core.identity)
        counter=forbid_generation(core);identity=snapshot(core.identity)
        write_new(directory/'core.json',identity)
        # Prefix preparation reuses the original frozen template and identity audit.
        scorer=attach_frozen_gemma(core)
        code_audit=audit_codes(core.processor.tokenizer)
        write_new(directory/'code_audit.json',code_audit)
        backend=NextCodeBackend(core.model,core.processor.tokenizer.pad_token_id,core.device)
        controller_start=perf_counter_ns()
        for i,row in enumerate(rows):
            write_new(directory/('task_%02d_started.json'%i),{'task_id':row['task_id'],'view_sha256':digest(row['view'])})
            remaining=lambda:min(Budget().study_wall_ms-elapsed(),Budget().controller_wall_ms-controller_ms())
            record=score_development(row['view'],scorer.encode_prefix,code_audit['token_ids'],backend,ledger,remaining)
            record['task_id']=row['task_id'];records.append(record)
            write_new(directory/('task_%02d.json'%i),record)
            print(canonical({'task_id':row['task_id'],'status':record['status'],
                             'winner':record.get('summary',{}).get('winner')}),flush=True)
            if record['status']!='COMPLETE':raise RuntimeError('first partial failure; preserve and stop')
            if any(type(p['peak_accelerator_memory_bytes']) is not int or p['peak_accelerator_memory_bytes']<=0
                   for p in record['passes']):raise ValueError('actual peak VRAM receipt required')
        audit=core.audit()
        if core.identity!=identity:audit['unchanged']=False
    except Exception as exc:
        error={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    if core is not None and not audit:
        try:audit=core.audit()
        except Exception as exc:audit={'unchanged':False,'error':str(exc)}
    complete=error is None and len(records)==12 and all(r['status']=='COMPLETE' for r in records)
    wall=controller_ms();total=elapsed()
    verdict=evaluate_development(records,audit.get('unchanged'),complete,counter['calls'],wall,total)
    report={'schema':SCHEMA,'status':'COMPLETE' if complete else 'INCOMPLETE','decision':verdict,
            'ledger':ledger,'observations':len(records),'accounting_complete':complete,'core_audit':audit,
            'controller_wall_ms':wall if controller_start is not None else None,'whole_study_ms':total,
            'startup_ms':None if controller_start is None else (controller_start-began)/1e6,
            'generated_calls':counter['calls'],'generated_tokens':0 if counter['calls']==0 else None,
            'tool_calls':0,'frontier_calls':0,'new_training':False,'sealed_data_opened':False,
            'fresh_validation_opened':False,'development_only':True,'error':error,
            'energy_j':None,'flops':None,'cost_money':None,
            'ledger_semantics':'attempted prefix input costs plus completed label scores; incomplete missing work UNKNOWN'}
    write_new(directory/'report.json',report)
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.glob('*.json'))}
    write_new(directory/'terminal.json',{'files':pins,'complete':complete,'no_replacement':True,
                                        'decision':verdict['verdict'],'development_only':True})
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check-registration',action='store_true')
    parser.add_argument('--tokenizer-readiness',action='store_true');parser.add_argument('--directory');parser.add_argument('--frozen-head')
    args=parser.parse_args()
    if args.check_registration:
        reg,rows=registration();print(canonical({'registration_valid':True,'development_rows':len(rows),'model_inference':False}))
    elif args.tokenizer_readiness:print(canonical(tokenizer_readiness()))
    else:
        if not args.directory or not args.frozen_head:parser.error('first development requires directory/frozen-head')
        result=run(args.directory,args.frozen_head);print(canonical(result))
        raise SystemExit(0 if result['decision']['verdict']=='PASS' else 2)
