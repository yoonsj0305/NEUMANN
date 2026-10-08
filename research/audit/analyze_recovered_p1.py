"""Audit existing notebook outputs and an embedded first ZIP; never run a model.

The notebook session remains off. Printed diagnostic JSON is documentary
evidence, not a substitute for a missing original archive or independent replay.
"""
from __future__ import annotations
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
RECOVERY = ROOT / 'research/evidence/p1-recovered'
P17_NAME = 'NEUMANN_P17_FIRST_EVIDENCE_RECOVERED.zip'
P17_SHA = '97f84b6e5f0980fdc815dbb3678502e0e23b1459af1b68e1630361379a254bad'
EARLY_ARCHIVES = {
    'P1.1': ('P11', 52833, '6bdc2cc9435cefd8a3e99d1d0bc3589bd3b6ad84e50be83db877b1dde769e3ec'),
    'P1.2-dev': ('P12', 83071, 'b27748d76b8abdba24ab11ad85f25eb4012c8c9593a12a83590bfbf8666c98ba'),
    'P1.2-validation': ('P12_VALIDATION', 93637, '362b13d7d7006ea1c55ad33788acd11d1712e94c081d59d52b28581d3abe3444'),
    'P1.4': ('P14', 61736, '7f819cd1dd26dc94ca690b4be3e2e365b7f65882900caff78e30e3e1c647af52'),
    'P1.5': ('P15', 39438, '4e252ab6a67c0988d31fb148647ef7124b2543b5f52abfd84987b3a164ffea5d'),
    'P1.6': ('P16', 39521, '7a217717513ddac16aa54a00e28aec62397ff2d356dbd689fe42d4952b1862d4'),
}
BLOCKS = {
    'P1.8': 'BEGIN_P1_8_COPY_PASTE_RESULT.txt',
    'P1.9': 'BEGIN_P1_9_COPY_PASTE_RESULT.txt',
    'P1.10': 'BEGIN_P1_10_INTERRUPTED_PARTIAL_DIAGNOSTIC.txt',
    'P1.11': 'BEGIN_P1_11_NOT_EVALUATED_DIAGNOSTIC.txt',
    'P1.11.1': 'P1111_RETAINED_NOTEBOOK_OUTPUT.txt',
}

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def printed_json(path: Path) -> dict:
    raw = path.read_bytes()
    text = raw.decode('utf-8')
    lines = text.splitlines()
    if not lines[0].startswith('===== BEGIN P1.') or not lines[-1].startswith('===== END P1.'):
        raise ValueError('Not a scoped retained diagnostic block')
    result = json.loads('\n'.join(lines[1:-1]))
    if not isinstance(result, dict):
        raise ValueError('Unexpected diagnostic shape')
    return result

def verify_early_archive(study: str) -> dict:
    """Compare original documentary pins, archive members and retained reports.

    No archive bootstrap, model code or receipt replay is executed here.
    Historical fresh designation does not grant current fresh status.
    """
    code, expected_bytes, expected_sha = EARLY_ARCHIVES[study]
    path = RECOVERY / f'NEUMANN_{code}_FIRST_EVIDENCE_RECOVERED.zip'
    raw = path.read_bytes()
    if len(raw) != expected_bytes or digest(raw) != expected_sha:
        raise ValueError('Historical archive identity mismatch: ' + study)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or archive.testzip() is not None:
            raise ValueError('Duplicate member or bad archive CRC')
        for info in archive.infolist():
            name = PurePosixPath(info.filename)
            if name.is_absolute() or '..' in name.parts or '\\' in info.filename or ':' in info.filename:
                raise ValueError('Unsafe historical member')
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Symlink historical member')
        manifest = json.loads(archive.read('archive_manifest.json'))
        if set(names) != set(manifest['members']) | {'archive_manifest.json'}:
            raise ValueError('Archive membership drift')
        for name, info in manifest['members'].items():
            payload = archive.read(name)
            if len(payload) != info['bytes'] or digest(payload) != info['sha256']:
                raise ValueError('Historical member identity drift: ' + name)
        directory = 'neumann_' + code.lower() + '_first'
        report_raw = archive.read(directory + '/report.json')
        report = json.loads(report_raw)
        setup = json.loads(archive.read(directory + '_setup.json'))
        tasks = [json.loads(archive.read(name)) for name in names
                 if name.startswith(directory + '/task_') and name.endswith('.json') and '_started' not in name]
        counts = None
        format_diagnosis = None
        score_diagnosis = None
        if study in ('P1.4', 'P1.5', 'P1.6'):
            counts = {'all_accepted': sum(t.get('accepted') is True for t in tasks),
                      'arithmetic_accepted': sum(t.get('accepted') is True for t in tasks[:4]),
                      'csp_accepted': sum(t.get('accepted') is True for t in tasks[4:8])}
            format_diagnosis = {'nonexecuted': sum(t.get('executed') is False for t in tasks),
                'errors': dict(Counter(t.get('error') or 'NONE' for t in tasks)),
                'nonexecuted_is_not_proof_of_semantic_impossibility': True}
        if study == 'P1.2-validation':
            score_diagnosis = {
                'task_rows': len(tasks),
                'all_loo_winners_stable': all(t['summary']['all_loo_winners_stable'] for t in tasks),
                'maximum_numeric_delta_nats': max(t['numeric_delta_nats'] for t in tasks),
                'original_compatible_routes': report['decision']['compatible_routes'],
                'incompatible_planning_rows': [{'task_id': t['task_id'],
                    'winner': t['summary']['winner'], 'margin_nats': t['summary']['margin_nats'],
                    'loo_stable': t['summary']['all_loo_winners_stable']}
                    for t in tasks[8:] if t['summary']['winner'] != 'CSP'],
                'stability_is_not_semantic_competence': True,
            }
        return {
            'source': str(path), 'archive_sha256': expected_sha, 'archive_bytes': len(raw),
            'archive_members': len(names), 'all_manifested_members_verified': True,
            'original_runtime_head': manifest['runtime_head'], 'original_report_sha256': digest(report_raw),
            'original_status': report['status'], 'original_verdict': report['decision'],
            'original_accounting_complete': report['accounting_complete'],
            'original_setup_status': setup['status'], 'original_replay_exit_code': setup['replay_exit_code'],
            'task_rows': len(tasks), 'original_whole_study_ms': report['whole_study_ms'],
            'original_startup_ms': report['startup_ms'],
            'original_cost_totals': report.get('cost_totals', report.get('ledger')),
            'original_task_acceptance': counts, 'current_designation': 'OPENED_DEVELOPMENT_ONLY',
            'format_diagnosis': format_diagnosis, 'score_diagnosis': score_diagnosis,
            'new_model_calls': 0, 'integrity_verification_is_not_semantic_replay': True,
        }

def verify_p17(path: Path) -> dict:
    raw = path.read_bytes()
    if len(raw) != 86633 or digest(raw) != P17_SHA:
        raise ValueError('Historical P1.7 archive identity mismatch')
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or archive.testzip() is not None:
            raise ValueError('Duplicate member or bad archive CRC')
        manifest = json.loads(archive.read('archive_manifest.json'))
        if set(names) != set(manifest['members']) | {'archive_manifest.json'}:
            raise ValueError('Archive membership drift')
        for name, info in manifest['members'].items():
            payload = archive.read(name)
            if len(payload) != info['bytes'] or digest(payload) != info['sha256']:
                raise ValueError('Historical member identity drift: ' + name)
        report = json.loads(archive.read('neumann_p17_first/report.json'))
        setup = json.loads(archive.read('neumann_p17_first_setup.json'))
        tasks = [json.loads(archive.read(f'neumann_p17_first/task_{i:02d}.json')) for i in range(12)]
        registration = json.loads(archive.read('neumann_p17_first/manifest.json'))['registration']
        return {
            'source': str(path), 'archive_sha256': P17_SHA, 'archive_bytes': len(raw),
            'archive_members': len(names), 'all_manifested_members_verified': True,
            'original_runtime_head': manifest['runtime_head'],
            'original_report_sha256': digest(archive.read('neumann_p17_first/report.json')),
            'original_verdict': report['decision'], 'original_accounting_complete': report['accounting_complete'],
            'original_setup_status': setup['status'], 'original_replay_exit_code': setup['replay_exit_code'],
            'task_rows': len(tasks), 'original_accepted': sum(row.get('accepted') is True for row in tasks),
            'unique_accepted': sum(row.get('accepted') is True for row in tasks[:8]),
            'ambiguous_accepted': sum(row.get('accepted') is True for row in tasks[8:]),
            'original_whole_study_ms': report['whole_study_ms'],
            'original_cost_totals': report['cost_totals'],
            'registered_ambiguous_forwards': registration['gate']['ambiguous_neural_forward_calls_exact'],
            'new_model_calls': 0, 'new_replay_of_failed_semantic_receipts': False,
            'integrity_verification_is_not_semantic_replay': True,
        }

def verify_p13_archive() -> dict:
    """P1.3 used terminal/source pins rather than archive_manifest.json."""
    path = RECOVERY/'NEUMANN_P13_FIRST_CONTRACT_EVIDENCE_RECOVERED.zip'
    raw = path.read_bytes()
    expected_sha = '5a578c9dcc4f4b4182a3dd3a7a4cde1974c98deea22d2ea123869b3fe394facd'
    if len(raw)!=130662 or digest(raw)!=expected_sha:
        raise ValueError('Original P1.3 workflow archive identity mismatch')
    directory = 'neumann_p13_first_contract'
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names)!=len(set(names)) or archive.testzip() is not None:
            raise ValueError('P1.3 archive CRC/membership drift')
        terminal = json.loads(archive.read(directory+'/terminal.json'))
        registration_name = 'source/docs/experiments/control_plane_p13.preregister.json'
        registration = json.loads(archive.read(registration_name))
        expected_names = {directory+'/'+n for n in terminal['files']}
        expected_names.add(directory+'/terminal.json')
        expected_names.update('source/'+n for n in registration['source_sha256'])
        expected_names.add(registration_name)
        if set(names)!=expected_names:
            raise ValueError('P1.3 closed archive membership drift')
        for name, expected in terminal['files'].items():
            if digest(archive.read(directory+'/'+name))!=expected:
                raise ValueError('P1.3 original receipt hash drift')
        for name, expected in registration['source_sha256'].items():
            if digest(archive.read('source/'+name))!=expected:
                raise ValueError('P1.3 original source pin drift')
        report_raw = archive.read(directory+'/report.json')
        report = json.loads(report_raw)
        return {'source': str(path), 'archive_sha256': expected_sha, 'archive_bytes': len(raw),
                'archive_members': len(names), 'all_manifested_members_verified': True,
                'hash_binding_kind': 'Exact workflow-announced archive plus51 terminal receipt pins and33 preregistered source pins',
                'original_runtime_head': report['source_head'], 'original_report_sha256': digest(report_raw),
                'original_status': report['status'], 'original_verdict': report['decision'],
                'original_replay_exit_code': 0, 'original_replay_source': 'P13_REPLAY original workflow log',
                'task_rows': report['observations'], 'original_whole_study_ms': report['whole_study_ms'],
                'cost_scope': report['cost_scope'], 'new_model_calls': 0,
                'initial_ci_failure_science_step': 'SKIPPED; no experiment executed',
                'source_workflow_run': 37184100179, 'source_workflow_job': 111382340094,
                'outer_GitHub_artifact_digest_is_not_inner_archive_digest': True,
                'current_designation': 'OPENED_DEVELOPMENT_ONLY; engineering interface result'}

def replay_p13_archive() -> dict:
    meta = verify_p13_archive()
    receipt = RECOVERY/'P13_RECOVERED_MODEL_FREE_REPLAY.json'
    if receipt.exists():
        raise FileExistsError('Independent replay receipt already retained')
    target = RECOVERY/'recovered-p13-replay-copy'
    target.mkdir(exist_ok=True)
    prefix = 'neumann_p13_first_contract/'
    with zipfile.ZipFile(meta['source']) as archive:
        for name in archive.namelist():
            if name.startswith(prefix):
                destination = target/PurePosixPath(name).name
                payload = archive.read(name)
                if destination.exists():
                    if destination.read_bytes()!=payload:
                        raise ValueError('Existing replay-copy bytes changed')
                else:
                    with destination.open('xb') as stream:
                        stream.write(payload)
    from experiments.control_plane_p13_first import replay
    result = {'existing_replay': replay(target), 'source_archive_sha256': meta['archive_sha256'],
              'neural_forwards': 0, 'first_run_not_replaced': True,
              'existing_replay_source_sha256': digest((ROOT/'experiments/control_plane_p13_first.py').read_bytes())}
    with receipt.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return result

def p1111_summary(bundle: dict) -> dict:
    tasks = bundle['tasks']
    if len(tasks) != 12 or any(not row['completed'] for row in tasks):
        raise ValueError('P1.11.1 diagnostic coverage mismatch')
    raw_correct = sum(row['raw_top_correct'] is True for row in tasks)
    selected_wrong = [row['task_id'] for row in tasks if row['selected_correct'] is False]
    abstained_correct = [row['task_id'] for row in tasks if row['raw_top_correct'] is True and row['selected_candidate'] is None]
    return {
        'completed_tasks': len(tasks), 'original_accepted': sum(row['accepted'] is True for row in tasks),
        'retained_raw_top_correct': raw_correct,
        'threshold_only_correctness_ceiling': raw_correct,
        'registered_accepted_floor': 9,
        'threshold_only_cannot_reach_registered_floor': raw_correct < 9,
        'selected_wrong_tasks': selected_wrong, 'abstained_raw_correct_tasks': abstained_correct,
        'maximum_wrong_selected_margin': max(row['selector_decision']['margin_cosine'] for row in tasks if row['selected_correct'] is False),
        'original_forward_calls': bundle['derived_summary']['neural_forward_calls'],
        'diagnostic_kind': 'RETAINED_PRINTED_JSON_ONLY; raw P1111 ZIP not recovered',
        'new_model_calls': 0, 'thresholds_changed': False,
    }

def replay_early_archives() -> dict:
    """Run the already existing model-free replay against a verified copy.

    The original archives and historical failed replay receipts are unchanged.
    This recomputes retained score aggregation or deterministic original-goal
    checks; it does not obtain model scores or time a candidate architecture.
    """
    copy_root = RECOVERY/'recovered-early-p1-replay-copy'
    copy_root.mkdir(exist_ok=False)
    results = {}
    for study in EARLY_ARCHIVES:
        meta = verify_early_archive(study)
        code = EARLY_ARCHIVES[study][0].lower()
        directory = 'neumann_' + code + '_first'
        target = copy_root/directory
        target.mkdir()
        with zipfile.ZipFile(meta['source']) as archive:
            for name in archive.namelist():
                if name.startswith(directory + '/'):
                    relative = PurePosixPath(name).relative_to(directory)
                    destination = target.joinpath(*relative.parts)
                    if not destination.resolve().is_relative_to(target.resolve()):
                        raise ValueError('Replay-copy path escaped intended directory')
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with destination.open('xb') as stream:
                        stream.write(archive.read(name))
        module = 'experiments.control_plane_' + code + '_replay'
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES='')
        process = subprocess.run([sys.executable, '-X', 'utf8', '-m', module,
                                  '--directory', str(target)], cwd=ROOT,
                                 env=environment, capture_output=True, timeout=60)
        stdout, stderr = process.stdout.decode('utf-8'), process.stderr.decode('utf-8')
        with (copy_root/(code+'_stdout.txt')).open('x', encoding='utf-8') as stream:
            stream.write(stdout)
        with (copy_root/(code+'_stderr.txt')).open('x', encoding='utf-8') as stream:
            stream.write(stderr)
        replay_result = json.loads(stdout) if process.returncode == 0 else None
        if replay_result is not None and replay_result.get('model_inference') is not False:
            raise ValueError('Replay must explicitly prohibit model inference')
        results[study] = {'exit_code': process.returncode, 'result': replay_result,
                          'original_replay_exit_code': meta['original_replay_exit_code'],
                          'original_frozen_verdict': meta['original_verdict'],
                          'existing_replay_module': module,
                          'existing_replay_source_sha256': digest((ROOT/(module.replace('.', '/')+'.py')).read_bytes()),
                          'copied_archive_sha256': meta['archive_sha256'],
                          'original_archive_still_matches': digest(Path(meta['source']).read_bytes()) == meta['archive_sha256'],
                          'stderr_sha256': digest(process.stderr)}
    result = {'schema': 'neumann.p1-recovered-model-free-replay.v1', 'results': results,
              'model_calls': 0, 'neural_forwards': 0, 'optimization_calls': 0,
              'deterministic_original_goal_checks_executed': True,
              'historical_verdicts_changed': False, 'fresh_evaluation': False}
    with (RECOVERY/'P1_RECOVERED_MODEL_FREE_REPLAY.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return result

def analyze() -> dict:
    outputs = {}
    bundles = {}
    for study, name in BLOCKS.items():
        path = RECOVERY/name
        bundles[study] = printed_json(path)
        outputs[study] = {'path': str(path), 'sha256': digest(path.read_bytes()),
                          'bytes': path.stat().st_size, 'kind': 'RETAINED_PRINTED_DIAGNOSTIC_NOT_RAW_ARCHIVE'}
    replay_path = RECOVERY/'P1_RECOVERED_MODEL_FREE_REPLAY.json'
    replay = None
    if replay_path.is_file():
        replay = {'path': str(replay_path), 'sha256': digest(replay_path.read_bytes()),
                  'result': json.loads(replay_path.read_bytes()),
                  'not_reexecuted_by_analysis': True}
    return {
        'schema': 'neumann.recovered-p1-evidence.v1',
        'notebook': 'https://www.kaggle.com/code/universe7475/notebookf7afb9b337/edit',
        'recovery_method': 'Visible retained output DOM and existing embedded data download; no cells run',
        'notebook_session_off': True,
        'P1.7': verify_p17(RECOVERY/P17_NAME),
        'P1.3': verify_p13_archive(),
        'early_archives': {study: verify_early_archive(study) for study in EARLY_ARCHIVES},
        'current_model_free_replay_receipt': replay,
        'printed_outputs': outputs,
        'P1.11.1_threshold_diagnosis': p1111_summary(bundles['P1.11.1']),
        'global_questions_closed': [], 'new_model_calls': 0, 'new_solver_calls': 0,
        'fresh_data_created': False, 'sealed_payload_access': False,
        'decision': 'HOLD_LEARNING; preserve first outcomes',
    }

if __name__ == '__main__':
    if '--replay-p13' in sys.argv[1:]:
        print(json.dumps(replay_p13_archive(), ensure_ascii=False))
        raise SystemExit(0)
    if '--replay-early' in sys.argv[1:]:
        result = replay_early_archives()
        print(json.dumps({study: {'exit_code': row['exit_code'], 'result': row['result']}
                          for study, row in result['results'].items()}, ensure_ascii=False))
        raise SystemExit(0 if all(row['exit_code']==0 for row in result['results'].values()) else 1)
    result = analyze()
    (ROOT/'research/audit/P1_RECOVERY_ANALYSIS.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'archive_members_verified': result['P1.7']['archive_members'],
                      'P17_original_verdict': result['P1.7']['original_verdict'],
                      'P1111_diagnosis': result['P1.11.1_threshold_diagnosis']}, ensure_ascii=False))
