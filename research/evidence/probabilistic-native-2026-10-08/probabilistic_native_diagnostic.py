"""Bounded opened G0-A diagnostic. Native algorithms, zero learned inference.

The supplied-quotient arm is an optimistic lower bound, NOT a deployable
NEUMANN path. All native paths have the same compilation and reuse rights.
"""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import os
import platform
import re
try:
    import resource
except ImportError:  # Source-contract unit checks on the Windows host, no solving.
    resource = None
import statistics
import subprocess
import sys
import time
import traceback

ROOT = Path('/kaggle/working/neumann_probabilistic')
sys.set_int_max_str_digits(100_000)
ROUTES = ['sparse_exact', 'sparse_exact_topological', 'sparse_parametric_bisim',
          'dd_parametric', 'dd_parametric_bisim_sparse']


def write_first(path, obj):
    with path.open('x') as out:
        json.dump(obj, out, indent=2)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reduce_goal(values, expression):
    """Respect the PUBLIC original initial-state filter, never select one arbitrarily."""
    assert expression['op'] == 'filter' and expression['states'] == {'op': 'initial'}
    values = [Fraction(x) for x in values]
    assert values
    if expression['fun'] == 'max':
        return str(max(values))
    if expression['fun'] == 'values':
        assert len(values) == 1, 'Multiple initial values require a vector reference, not a scalar guess'
        return str(values[0])
    raise ValueError('Unsupported goal filter; refuse to change the original goal')


def worker(request_path):
    worker_start = time.perf_counter_ns()
    request = json.loads(Path(request_path).read_text())
    assert set(request['case']) == {'case_id', 'family', 'file', 'goal', 'parameters',
                                    'file_sha256', 'goal_expression'}
    assert resource is not None, 'Native worker requires the registered Linux CPU environment'
    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024 ** 3, 8 * 1024 ** 3))
    sys.path.insert(0, str(ROOT / 'deps'))
    import stormpy
    bootstrap = (time.perf_counter_ns() - worker_start) / 1e9
    startup_from_parent = (time.perf_counter_ns() - request['parent_launch_ns']) / 1e9
    outdir = Path(request['outdir'])
    case, route, source_format = request['case'], request['route'], request['format']
    native = request['native']
    records = []
    for repeat in range(4):
        row = {'case_id': case['case_id'], 'route': route, 'format': source_format,
               'repeat': repeat, 'condition': 'cold_worker' if repeat == 0 else 'resident_fresh_request',
               'bootstrap_seconds': bootstrap, 'stage_seconds': {}, 'status': 'STARTED',
               'startup_from_parent_seconds': startup_from_parent, 'learned_discovery': False}
        started = time.perf_counter_ns()
        try:
            stage = time.perf_counter_ns()
            if source_format == 'jani':
                path = ROOT / 'inputs' / case['family'] / case['file']
                assert sha(path) == case['file_sha256']
                symbolic, props = stormpy.parse_jani_model(str(path))
            else:
                path = ROOT / 'native-inputs' / case['family'] / native['prism']['name']
                property_path = ROOT / 'native-inputs' / case['family'] / native['properties']['name']
                assert sha(path) == native['prism']['sha256']
                assert sha(property_path) == native['properties']['sha256']
                symbolic = stormpy.parse_prism_program(str(path))
                text = re.sub(r'//[^\n]*', '', property_path.read_text())
                props = stormpy.parse_properties_for_prism_program(text, symbolic)
            props = [p for p in props if p.name == case['goal']]
            assert len(props) == 1
            constants = ','.join(f'{p["name"]}={p["value"]}' for p in case['parameters'])
            description, props = stormpy.preprocess_symbolic_input(symbolic, props, constants)
            symbolic = description.as_jani_model() if source_format == 'jani' else description.as_prism_program()
            if source_format == 'jani':
                props = stormpy.eliminate_reward_accumulations(symbolic, props)
            row['stage_seconds']['parse_bind_goal'] = (time.perf_counter_ns() - stage) / 1e9
            row['formula'] = str(props[0].raw_formula)
            stage = time.perf_counter_ns()
            if route.startswith('sparse_exact'):
                model = stormpy.build_sparse_exact_model(symbolic, props)
            elif route == 'sparse_parametric_bisim':
                model = stormpy.build_sparse_parametric_model(symbolic, props)
            else:
                model = stormpy.build_symbolic_parametric_model(symbolic, props)
            row['original_states'] = model.nr_states
            row['original_transitions'] = model.nr_transitions
            row['stage_seconds']['build_original'] = (time.perf_counter_ns() - stage) / 1e9
            stage = time.perf_counter_ns()
            if route == 'sparse_parametric_bisim':
                model = stormpy.perform_sparse_bisimulation(model, props, stormpy.BisimulationType.STRONG)
            elif route == 'dd_parametric_bisim_sparse':
                model = stormpy.perform_symbolic_bisimulation(model, props, stormpy.QuotientFormat.SPARSE)
            elif route == 'dd_parametric':
                model = stormpy.transform_to_sparse_model(model)
            row['stage_seconds']['native_abstraction_or_conversion'] = (time.perf_counter_ns() - stage) / 1e9
            row['executed_states'], row['executed_transitions'] = model.nr_states, model.nr_transitions
            environment = stormpy.Environment()
            environment.solver_environment.set_force_exact(True)
            if route == 'sparse_exact_topological':
                environment.solver_environment.set_linear_equation_solver_type(stormpy.EquationSolverType.topological)
            stage = time.perf_counter_ns()
            result = stormpy.model_checking(model, props[0], only_initial_states=True, environment=environment)
            vals = [str(result.at(i)) for i in model.initial_states]
            row['original_goal_output'] = reduce_goal(vals, case['goal_expression'])
            row['initial_state_count'] = len(vals)
            row['stage_seconds']['execute_restore'] = (time.perf_counter_ns() - stage) / 1e9
            row['request_seconds'] = (time.perf_counter_ns() - started) / 1e9
            if repeat == 0:
                row['cold_first_output_seconds'] = (time.perf_counter_ns() - request['parent_launch_ns']) / 1e9
            row['status'] = 'OUTPUT_OBSERVED_NOT_YET_JUDGED'
            # Both arms receive the SAME already compiled native quotient and property.
            # No answer cache; actually solve again. This is a repeated-input control.
            if 'bisim' in route:
                reuse = []
                for arm in ['NATIVE_COMPILED_REUSE', 'FREE_VALID_PERSPECTIVE_LOWER_BOUND']:
                    for trial in range(4):
                        stage = time.perf_counter_ns()
                        res = stormpy.model_checking(model, props[0], only_initial_states=True, environment=environment)
                        goal = reduce_goal([str(res.at(i)) for i in model.initial_states], case['goal_expression'])
                        reuse.append({'arm': arm, 'trial': trial, 'warmup': trial == 0,
                                      'seconds': (time.perf_counter_ns() - stage) / 1e9, 'output': goal})
                row['compiled_reuse_checks'] = reuse
            row['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        except Exception as exc:
            row.update(status='NOT_VERIFIED', error_type=type(exc).__name__, error=str(exc),
                       traceback=traceback.format_exc(), request_seconds=(time.perf_counter_ns() - started) / 1e9)
        write_first(outdir / f'repeat-{repeat}.json', row)
        records.append(row)
        if row['status'] == 'NOT_VERIFIED':
            break  # No rescue rerun under the same first contract.
    write_first(outdir / 'worker-completion-first.json', {'records': len(records), 'bootstrap_seconds': bootstrap})


def parent():
    contract_path = ROOT / 'probabilistic-native.preregister.json'
    contract = json.loads(contract_path.read_text())
    assert sha(ROOT / 'probabilistic_native_diagnostic.py') == contract['runner_sha256']
    assert sha(ROOT / 'source-cases-parent-first.json') == contract['parent_cases_sha256']
    cases = json.loads((ROOT / 'source-cases-parent-first.json').read_text())['cases']
    native_rows = {c['case_id']: c for c in json.loads((ROOT / 'native-sources-first.json').read_text())}
    results_dir = ROOT / 'native-first'
    results_dir.mkdir(exist_ok=False)
    write_first(results_dir / 'reservation-first.json', {'contract_sha256': sha(contract_path),
                'start_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'python': sys.version, 'platform': platform.platform(), 'cpu_count': os.cpu_count()})
    parent_started = time.perf_counter()
    jobs = []
    for index, case in enumerate(cases):
        formats = ['jani'] + (['prism'] if native_rows[case['case_id']]['prism'] else [])
        route_order = ROUTES[index % len(ROUTES):] + ROUTES[:index % len(ROUTES)]
        for source_format in formats:
            for route in route_order:
                jobs.append((case, source_format, route))
    rows = []
    for job_no, (case, source_format, route) in enumerate(jobs):
        if time.perf_counter() - parent_started >= contract['global_execution_seconds']:
            write_first(results_dir / 'global-budget-first.json', {'status': 'INCOMPLETE', 'unexecuted_jobs': len(jobs) - job_no})
            break
        folder = results_dir / f'{job_no:03d}-{case["case_id"]}-{source_format}-{route}'
        folder.mkdir()
        execution_case = {k: case[k] for k in ['case_id', 'family', 'file', 'goal', 'parameters',
                          'file_sha256', 'goal_expression']}
        request = {'case': execution_case, 'native': native_rows[case['case_id']],
                   'format': source_format, 'route': route, 'outdir': str(folder),
                   'parent_launch_ns': time.perf_counter_ns()}
        write_first(folder / 'request-first.json', request)
        command = [sys.executable, str(ROOT / 'probabilistic_native_diagnostic.py'), '--worker', str(folder / 'request-first.json')]
        environment = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
        started = time.perf_counter()
        try:
            with (folder / 'stdout-first.log').open('xb') as stdout, (folder / 'stderr-first.log').open('xb') as stderr:
                process = subprocess.run(command, stdout=stdout, stderr=stderr, env=environment,
                                         timeout=contract['per_job_seconds'], check=False)
            status = 'FINISHED' if process.returncode == 0 else 'PROCESS_FAILED'
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            status, returncode = 'TIMEOUT', None
        wall = time.perf_counter() - started
        attempts = []
        for path in sorted(folder.glob('repeat-*.json')):
            row = json.loads(path.read_text())
            judge_started = time.perf_counter()
            if row['status'] == 'OUTPUT_OBSERVED_NOT_YET_JUDGED':
                correct = Fraction(row['original_goal_output']) == Fraction(case['expected_exact'])
                checks = row.get('compiled_reuse_checks', [])
                correct = correct and all(Fraction(x['output']) == Fraction(case['expected_exact']) for x in checks)
                row['independent_reference_verdict'] = 'PASS' if correct else 'FAIL'
            else:
                row['independent_reference_verdict'] = 'NOT_VERIFIED'
            row['reference_judge_seconds'] = time.perf_counter() - judge_started
            row['raw_receipt_sha256'] = sha(path)
            attempts.append(row)
        receipt = {'job_no': job_no, 'case_id': case['case_id'], 'route': route, 'format': source_format,
                   'status': status, 'returncode': returncode, 'parent_wall_seconds': wall, 'attempts': attempts}
        write_first(folder / 'parent-receipt-first.json', receipt)
        rows.append(receipt)
        print(json.dumps({'job': job_no + 1, 'total': len(jobs), 'case': case['case_id'], 'format': source_format,
                          'route': route, 'status': status, 'seconds': round(wall, 4),
                          'verdicts': [x['independent_reference_verdict'] for x in attempts]}), flush=True)
        # A wrong goal is decisive rejection, not a candidate for cost screening.
        if any(x['independent_reference_verdict'] == 'FAIL' for x in attempts):
            write_first(results_dir / 'wrong-goal-stop-first.json', {'status': 'FAIL', 'job': job_no})
            break
    report = {'kind': 'OPENED_NATIVE_ACQUISITION_AND_REUSE_DIAGNOSTIC', 'rows': rows,
              'scheduled_jobs': len(jobs), 'executed_jobs': len(rows),
              'total_parent_wall_seconds': time.perf_counter() - parent_started,
              'learning': 'HOLD', 'new_intelligence_claim': False,
              'free_perspective_cost': 'OPTIMISTIC_LOWER_BOUND_WITH_UNKNOWN_DELIVERY_AND_CERTIFICATION',
              'energy_flops_money': 'UNKNOWN', 'G1_G2': 'NOT_ENTERED'}
    write_first(results_dir / 'report-first.json', report)
    print('NATIVE_DIAGNOSTIC_FIRST_COMPLETE', json.dumps({k: v for k, v in report.items() if k != 'rows'}), flush=True)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--worker':
        worker(sys.argv[2])
    else:
        parent()
