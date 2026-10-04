"""First-only fresh opened validation of the unchanged P1.2 architecture."""
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
from neumann1.control_plane_p1_contract import manifest as p1_manifest, validate_identity
from neumann1.control_plane_p12 import Budget, CODE_TOKEN_IDS, PERMUTATIONS, NextCodeBackend, CodePlan, audit_codes, plan_cost, prompt_for, score_development
from neumann1.control_plane_p12_validation import (SCHEMA, TASK_IDS, PUBLIC, REFERENCES, contract, evaluate_validation, validate_rows, validate_references, opened_development_rows)
from experiments.control_plane_p1_first import forbid_generation, write_new
from experiments.control_plane_p11_dev import tokenizer_readiness as original_tokenizer_readiness

ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = ROOT/'docs/experiments/control_plane_p12_validation.preregister.json'
ARCHITECTURE_FREEZE = ROOT/'docs/experiments/control_plane_p12_architecture.freeze.json'


def tokenizer_readiness():
    data = original_tokenizer_readiness()
    if tuple(data['token_ids']) != CODE_TOKEN_IDS: raise ValueError('original audited code IDs required')
    return data


def registration():
    data = json.loads(REGISTRATION.read_bytes())
    if data['contract'] != contract(): raise ValueError('P1.2 source/contract freeze drift')
    freeze = json.loads(ARCHITECTURE_FREEZE.read_bytes())
    if freeze['contract'] != contract()['architecture'] or freeze['origin_head'] != contract()['architecture_origin_head']:
        raise ValueError('original P1.2 architecture identity required')
    for name,expected in freeze['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected: raise ValueError('original architecture byte drift: '+name)
    for name, expected in data['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected: raise ValueError('source drift: '+name)
    rows = json.loads(PUBLIC.read_bytes())['rows']
    if tuple(r['task_id'] for r in rows) != TASK_IDS or any(set(r) != {'task_id','view'} for r in rows):
        raise ValueError('exact fresh input coverage required')
    if digest([r['view'] for r in rows]) != data['public_sha256']: raise ValueError('fresh public input drift')
    validate_rows(rows,opened_development_rows())
    return data, rows


def token_budget_readiness():
    """Exact frozen processor tokenization only; zero weights/forward scores."""
    from transformers import AutoProcessor, Gemma4Processor
    from neumann1.control_plane_p1_contract import MODEL
    _, rows = registration()
    processor = AutoProcessor.from_pretrained(MODEL['model_id'],revision=MODEL['model_revision'],token=False,trust_remote_code=False)
    if not isinstance(processor,Gemma4Processor): raise ValueError('original processor required')
    codes = audit_codes(processor.tokenizer)
    if tuple(codes['token_ids']) != CODE_TOKEN_IDS: raise ValueError('original code IDs required')
    totals = {k:0 for k in ('input_rows','score_rows','scored_tokens','evaluated_tokens','padded_tokens','forward_calls')}
    maximum = 0
    for row in rows:
        prefixes = []
        for mapping in PERMUTATIONS:
            ids = processor.apply_chat_template([{'role':'user','content':prompt_for(row['view'],mapping)}],
                tokenize=True,return_dict=True,add_generation_prompt=True,enable_thinking=False)['input_ids']
            if hasattr(ids,'tolist'): ids = ids.tolist()
            prefixes.append(tuple(ids[0] if ids and isinstance(ids[0],list) else ids))
        maximum = max(maximum,max(map(len,prefixes))+1)
        for size, order in ((4,prefixes),(1,prefixes),(4,list(reversed(prefixes)))):
            cost = plan_cost(CodePlan(tuple(order),CODE_TOKEN_IDS),size)
            for k,v in cost.items(): totals[k] += v
    if any(v>getattr(Budget(),k) for k,v in totals.items()): raise ValueError('fresh token budget exceeds frozen cap')
    return {'model_inference':False,'weights_loaded':False,'forward_scoring_calls':0,
            'registered_forward_calls_if_run':totals['forward_calls'],'planned_ledger':totals,'maximum_context_including_code':maximum}


def run(directory, frozen_head):
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=False)
    began = perf_counter_ns(); controller_start = None; core = None; audit = {}; counter = {'calls':0}; records = []; error = None
    elapsed = lambda: (perf_counter_ns()-began)/1e6
    controller_ms = lambda: 0. if controller_start is None else (perf_counter_ns()-controller_start)/1e6
    write_new(directory/'study_started.json', {'schema':SCHEMA,'frozen_head':frozen_head,'development_only':False})
    ledger = {k:0 for k in ('input_rows','score_rows','scored_tokens','evaluated_tokens','padded_tokens','forward_calls')}
    try:
        reg, rows = registration()
        write_new(directory/'manifest.json', {'registration':reg,'public_rows':rows,'frozen_head':frozen_head})
        if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() != frozen_head:
            raise ValueError('exact frozen source commit required')
        subprocess.run(['git','diff','--exit-code','HEAD','--'],cwd=ROOT,check=True,capture_output=True)
        for package, expected in p1_manifest()['runtime'].items():
            if version(package) != expected: raise ValueError('original runtime mismatch: '+package)
        from experiments.general_multiplier_accelerator_core import FrozenAcceleratorCore
        core = FrozenAcceleratorCore(); validate_identity(core.identity)
        counter = forbid_generation(core); identity = snapshot(core.identity)
        write_new(directory/'core.json', identity)
        scorer = attach_frozen_gemma(core); code_audit = audit_codes(core.processor.tokenizer)
        if tuple(code_audit['token_ids']) != CODE_TOKEN_IDS: raise ValueError('exact original audited code IDs required')
        write_new(directory/'code_audit.json', code_audit)
        backend = NextCodeBackend(core.model,core.processor.tokenizer.pad_token_id,core.device)
        controller_start = perf_counter_ns()
        for i, row in enumerate(rows):
            write_new(directory/('task_%02d_started.json'%i),{'task_id':row['task_id'],'view_sha256':digest(row['view'])})
            remaining = lambda: min(Budget().study_wall_ms-elapsed(),Budget().controller_wall_ms-controller_ms())
            record = score_development(row['view'],scorer.encode_prefix,code_audit['token_ids'],backend,ledger,remaining)
            record['task_id'] = row['task_id']; records.append(record)
            write_new(directory/('task_%02d.json'%i), record)
            print(canonical({'task_id':row['task_id'],'status':record['status'],
                             'winner':record.get('summary',{}).get('winner')}),flush=True)
            if record['status'] != 'COMPLETE': raise RuntimeError('first partial failure; preserve and stop')
            if any(type(p['peak_accelerator_memory_bytes']) is not int or p['peak_accelerator_memory_bytes'] <= 0
                   for p in record['passes']): raise ValueError('actual peak VRAM receipt required')
        audit = core.audit()
        if core.identity != identity: audit['unchanged'] = False
    except Exception as exc:
        error = {'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    if core is not None and not audit:
        try: audit = core.audit()
        except Exception as exc: audit = {'unchanged':False,'error':str(exc)}
    complete = error is None and len(records) == 12 and all(r['status'] == 'COMPLETE' for r in records)
    wall = controller_ms(); total = elapsed()
    references = json.loads(REFERENCES.read_bytes())['rows'] if complete else []
    verdict = evaluate_validation(records,references,audit.get('unchanged'),complete,counter['calls'],wall,total)
    report = {'schema':SCHEMA,'status':'COMPLETE' if complete else 'INCOMPLETE','decision':verdict,
              'ledger':ledger,'observations':len(records),'accounting_complete':complete,'core_audit':audit,
              'controller_wall_ms':wall if controller_start is not None else None,'whole_study_ms':total,
              'startup_ms':None if controller_start is None else (controller_start-began)/1e6,
              'generated_calls':counter['calls'],'generated_tokens':0 if counter['calls'] == 0 else None,
              'tool_calls':0,'frontier_calls':0,'new_training':False,'sealed_data_opened':False,
              'fresh_validation_opened':True,'fresh_validation_registered':True,'development_only':False,'historical_score_reuse':False,
              'error':error,'energy_j':None,'flops':None,'cost_money':None,
              'ledger_semantics':'attempted prefix input costs plus completed label scores; incomplete missing work UNKNOWN'}
    write_new(directory/'report.json', report)
    pins = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.glob('*.json'))}
    write_new(directory/'terminal.json',{'files':pins,'complete':complete,'no_replacement':True,
                                       'decision':verdict['verdict'],'development_only':False})
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); group = parser.add_mutually_exclusive_group()
    group.add_argument('--check-registration',action='store_true'); group.add_argument('--tokenizer-readiness',action='store_true')
    group.add_argument('--token-budget-readiness',action='store_true')
    parser.add_argument('--directory'); parser.add_argument('--frozen-head'); args = parser.parse_args()
    if args.check_registration:
        reg, rows = registration(); checks = validate_references(rows,json.loads(REFERENCES.read_bytes())['rows']); print(canonical({'registration_valid':True,'validation_rows':len(rows),'checker':checks,'model_inference':False}))
    elif args.tokenizer_readiness: print(canonical(tokenizer_readiness()))
    elif args.token_budget_readiness: print(canonical(token_budget_readiness()))
    else:
        if not args.directory or not args.frozen_head: parser.error('first validation requires directory/frozen-head')
        result = run(args.directory,args.frozen_head); print(canonical(result))
        raise SystemExit(0 if result['decision']['verdict'] == 'PASS' else 2)
