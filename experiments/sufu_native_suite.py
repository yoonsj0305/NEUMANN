"""Pinned, opened SuFu engineering suite. Bounded upstream checks, not G0/G1."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import os
import signal
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def run(root, registration_path):
    registration = json.loads(registration_path.read_text())
    assert registration['study'] == 'SUFU_NATIVE_OPENED_ENGINEERING_V1'
    assert sha(Path(__file__)) == registration['runner_sha256']
    receipt = json.loads((root / 'build-repair-receipt.json').read_text())
    executable = Path(receipt['executable'])
    assert sha(executable) == registration['executable_sha256']
    assert 'NDEBUG' not in (root / 'build-jsoncpp/executor/CMakeFiles/run.dir/flags.make').read_text()
    originals = json.loads((root / 'original-source-manifest.json').read_text())
    patches = json.loads((root / 'build-path-patches.json').read_text())
    allowed = {p['path']: p['after_sha256'] for p in patches}
    source = root / 'source'
    assert {n: sha(source / n) for n, h in originals.items() if sha(source / n) != h} == allowed
    benchmarks = registration['benchmarks']
    actual = sorted(p.relative_to(source).as_posix() for p in (source / 'benchmark').rglob('*.f')
                    if p.relative_to(source).as_posix() != 'benchmark/autolifter/autolifter-base.f')
    assert actual == [b['path'] for b in benchmarks]
    assert len(actual) == 290
    for b in benchmarks:
        assert sha(source / b['path']) == b['sha256']
    out = root / 'native-suite-first'
    assert not out.exists(), 'Preserve original first run; a recovery needs a new contract/root.'
    out.mkdir()
    save(out / 'registration.json', registration)
    started = time.perf_counter()
    outcomes = []
    for index, benchmark in enumerate(benchmarks):
        folder = out / f'{index:03}'
        folder.mkdir()
        target = folder / 'optimized.f'
        command = [str(executable), '--benchmark=' + str(source / benchmark['path']),
                   '--output=' + str(target), '--use_gurobi=false']
        begin = time.perf_counter()
        timeout = False
        with (folder / 'stdout').open('xb') as stdout, (folder / 'stderr').open('xb') as stderr:
            child = subprocess.Popen(command, cwd=source, stdout=stdout, stderr=stderr,
                                     start_new_session=True)
            try:
                child.wait(timeout=registration['timeout_seconds_per_case'])
            except subprocess.TimeoutExpired:
                timeout = True
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
        elapsed = time.perf_counter() - begin
        text = (folder / 'stdout').read_text(errors='replace')
        lines = text.strip().splitlines()
        success = (not timeout and child.returncode == 0 and lines and lines[-1] == 'Success'
                   and '\nincorrect\n' not in '\n' + text + '\n'
                   and target.exists() and target.stat().st_size > 0)
        status = ('UPSTREAM_BOUNDED_SUCCESS' if success else 'TIMEOUT' if timeout
                  else 'PROCESS_ERROR' if child.returncode != 0 else 'NOT_VERIFIED')
        record = {'index': index, 'benchmark': benchmark, 'status': status,
                  'command': command, 'exit_code': child.returncode, 'timeout': timeout,
                  'launch_to_exit_seconds': elapsed,
                  'stdout_sha256': sha(folder / 'stdout'), 'stderr_sha256': sha(folder / 'stderr'),
                  'optimized_sha256': sha(target) if target.exists() else None,
                  'output_existence_alone_is_not_success': True,
                  'universal_equivalence_proven': False}
        save(folder / 'record.json', record)
        outcomes.append(record)
        progress = {'completed': len(outcomes), 'total': len(benchmarks),
                    'counts': dict(Counter(r['status'] for r in outcomes)),
                    'elapsed_seconds': time.perf_counter() - started, 'last': benchmark['path']}
        with (out / 'progress.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(progress) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        print(json.dumps(progress), flush=True)
    report = {'study': registration['study'], 'status': 'COMPLETED_OPENED_ENGINEERING_ONLY',
              'benchmark_count': len(outcomes), 'counts': dict(Counter(r['status'] for r in outcomes)),
              'sequential_suite_seconds': time.perf_counter() - started,
              'recorded_worker_seconds': sum(r['launch_to_exit_seconds'] for r in outcomes),
              'recorded_first_setup_seconds': receipt['recorded_first_setup_seconds'],
              'recorded_repair_seconds': receipt['recorded_repair_seconds'],
              'bounded_verification_only': True, 'official_paper_score_replication': False,
              'gurobi_licensed_features_requested': False, 'fresh_eligible': 0,
              'neural_learning_performed': False, 'G0_passed': False, 'G1_admitted': False,
              'G2_admitted': False, 'unmeasured_resources': ['energy', 'FLOPs', 'RSS', 'economic_cost'],
              'outcomes': outcomes}
    save(out / 'report.json', report)
    save(out / 'manifest.json', {p.relative_to(out).as_posix(): sha(p)
                                for p in sorted(out.rglob('*')) if p.is_file()})
    print(json.dumps({k: v for k, v in report.items() if k != 'outcomes'}), flush=True)


if __name__ == '__main__':
    run(Path(sys.argv[1]), Path(sys.argv[2]))
