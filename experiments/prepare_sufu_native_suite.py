"""Freeze the entire public source list before any native suite evaluation."""
from pathlib import Path
import hashlib
import json
import zipfile

WORK = Path(__file__).resolve().parents[3]
ROOT = Path(__file__).resolve().parents[1]
C = WORK / 'Continuation'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    archive = C / 'SUFU_BUILD_FIRST/SUFU_BUILD_FIRST_RECORDS.zip'
    assert sha(archive.read_bytes()) == '4e1633e1b9a9fd9432574e5a1f819455681dbaf64b7276a0e75f6d3d5e09c64c'
    with zipfile.ZipFile(archive) as z:
        records = {i.filename: z.read(i) for i in z.infolist()}
    assert len(records) == 44
    receipt = json.loads(records['neumann-sufu/build-repair-receipt.json'])
    original = json.loads(records['neumann-sufu/original-source-manifest.json'])
    upstream = C / 'SUFU_SOURCE_FIRST/upstream'
    intake = json.loads((C / 'SUFU_SOURCE_FIRST/manifest.json').read_text())
    local_names = {f['path']: f['local_path'] for f in intake['files']}
    assert all(sha((upstream / local_names[name]).read_bytes()) == value for name, value in original.items())
    for folder in ('setup', 'setup-jsoncpp-repair'):
        for event in json.loads(records[f'neumann-sufu/{folder}/events.json']):
            i = json.loads(records[f'neumann-sufu/{folder}/events.json']).index(event)
            assert sha(records[f'neumann-sufu/{folder}/{i:02}.stdout']) == event['stdout_sha256']
            assert sha(records[f'neumann-sufu/{folder}/{i:02}.stderr']) == event['stderr_sha256']
    preflight = json.loads(records['neumann-sufu/preflight-sum/report.json'])
    assert preflight['status'] == 'UPSTREAM_REPORTED_SUCCESS_BOUNDED_ONLY'
    target = C / 'SUFU_NATIVE_PREPARATION'
    target.mkdir()
    runner = (ROOT / 'experiments/sufu_native_suite.py').read_bytes()
    benchmarks = [{'path': p.relative_to(upstream).as_posix(), 'sha256': sha(p.read_bytes())}
                  for p in sorted((upstream / 'benchmark').rglob('*.f'), key=lambda p: p.relative_to(upstream).as_posix())
                  if p.relative_to(upstream).as_posix() != 'benchmark/autolifter/autolifter-base.f']
    assert len(benchmarks) == 290
    registration = {'study': 'SUFU_NATIVE_OPENED_ENGINEERING_V1',
                    'purpose': 'Strong existing structural synthesis baseline engineering intake; not economic headroom.',
                    'commit': 'c2b3ff0637460c568b0533f992007278f88d0f55',
                    'runner_sha256': sha(runner), 'executable_sha256': receipt['executable_sha256'],
                    'timeout_seconds_per_case': 30, 'repeats': 1,
                    'selection': 'all 290 pinned benchmark/**/*.f except the author-excluded grammar module',
                    'excluded_before_execution': [{'path': 'benchmark/autolifter/autolifter-base.f',
                        'reason': 'Shared grammar definitions; not a runnable benchmark; author collector excludes this.'}],
                    'seed': 'Upstream default Env RNG(0); all randomness not established fixed.',
                    'modified_algorithm_sources': 0, 'use_gurobi': False,
                    'exposure': 'Entire public source and upstream cached results opened; sum preflight run.',
                    'published_score_is_not_our_score': True, 'bounded_checks_are_not_universal_proofs': True,
                    'fresh_eligible': 0, 'G0_passed': False, 'G1_admitted': False, 'G2_admitted': False,
                    'no_followup_retuning_or_selective_replacement': True,
                    'benchmarks': benchmarks}
    raw = (json.dumps(registration, indent=2) + '\n').encode()
    (target / 'registration.json').write_bytes(raw)
    (target / 'runner.py').write_bytes(runner)
    with zipfile.ZipFile(target / 'inputs.zip', 'x', zipfile.ZIP_DEFLATED) as z:
        z.writestr('registration.json', raw)
        z.writestr('runner.py', runner)
    freeze = {'registration_sha256': sha(raw), 'runner_sha256': sha(runner),
              'payload_sha256': sha((target / 'inputs.zip').read_bytes()),
              'build_records': {'members': 44, 'sha256': sha(archive.read_bytes()),
                                'original_source_files_checked': len(original)},
              'execution_started': False}
    (target / 'freeze.json').write_text(json.dumps(freeze, indent=2) + '\n')
    print(json.dumps(freeze, indent=2))


if __name__ == '__main__':
    main()
