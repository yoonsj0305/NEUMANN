"""Frozen original-upstream baseline integration. Never confers a G0/G1 verdict.

Runs the published small suite and five declared list/auxiliary-state diagnostics.
Synduce's reported solution is not independently certified by exit status alone.
"""
from pathlib import Path
import hashlib
import json
import os
import signal
import subprocess
import time

PIN = 'b5c1d1611d3fbf5d8cdf9a23fde52c2cbba95a89'
CASES = [
    ('list/sum.ml', '', 'REALIZABLE'),
    ('ptree/sum.ml', '', 'REALIZABLE'),
    ('tree/sum.ml', '', 'REALIZABLE'),
    ('tailopt/sum.ml', '', 'REALIZABLE'),
    ('treepaths/sum.ml', '', 'REALIZABLE'),
    ('treepaths/height.ml', '--se2gis', 'REALIZABLE'),
    ('treepaths/maxPathWeight.ml', '', 'REALIZABLE'),
    ('ptree/mul.ml', '', 'REALIZABLE'),
    ('tree/max.ml', '', 'REALIZABLE'),
    ('tree/min.pmrs', '', 'REALIZABLE'),
    ('tree/maxtree2.pmrs', '', 'REALIZABLE'),
    ('list/sumodds.ml', '', 'REALIZABLE'),
    ('list/prod.ml', '', 'REALIZABLE'),
    ('list/poly.ml', '', 'REALIZABLE'),
    ('list/hamming.ml', '', 'REALIZABLE'),
    ('list/sumevens.ml', '', 'REALIZABLE'),
    ('list/len.ml', '', 'REALIZABLE'),
    ('list/last.pmrs', '', 'REALIZABLE'),
    ('constraints/sortedlist/count_lt.ml', '', 'REALIZABLE'),
    ('constraints/bst/count_lt.ml', '-NB', 'REALIZABLE'),
    ('constraints/ensures/mps_no_ensures.ml', '-B', 'REALIZABLE'),
    ('list/largest_diff_sorted_list_nohead.ml', '--se2gis', 'REALIZABLE'),
    ('list/poly_no_fac.ml', '--se2gis', 'REALIZABLE'),
    ('unrealizable/po_sorted.ml', '', 'UNREALIZABLE'),
    ('list/mps.ml', '', 'REALIZABLE'),
    ('list/mts.ml', '', 'REALIZABLE'),
    ('list/mss.ml', '', 'REALIZABLE'),
    ('list/mps_no_sum.ml', '', 'UPSTREAM_LIFTING_DIAGNOSTIC'),
    ('lifting/mssl.ml', '', 'UPSTREAM_LIFTING_DIAGNOSTIC'),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registration(source: Path):
    return {'experiment_id': 'FULL_SYNDuce_BASELINE_INTEGRATION_V1',
            'kind': 'OPENED_UPSTREAM_ENGINEERING_BASELINE_NOT_HEADROOM_OR_LEARNING',
            'source_commit': PIN, 'cases': [
                {'path': path, 'options': options.split(), 'expected': expected,
                 'source_sha256': sha(source / 'benchmarks' / path)}
                for path, options, expected in CASES],
            'repetitions': 3, 'external_timeout_seconds': 60,
            'solver': 'cvc5', 'solver_version': 'record_actual_apt_version_before_execution',
            'execution_order': 'case_order_then_repeat_0_1_2_sequential_single_process_groups',
            'scope': 'Original programs including repr,target and source invariants; tool reports retained verbatim',
            'cost_scope': 'subprocess launch,upstream solving,output retrieval and exit; setup/build is separate investment',
            'cost_not_included': ['independent original task certification', 'application queries',
                                  'research labour', 'energy', 'money', 'neural training'],
            'status_rules': {'no_solution_timeout': 'NOT_EVALUATED_OR_NOT_SOLVED_NEVER_WRONG_BY_DEFAULT',
                             'solution_json': 'UPSTREAM_REPORTED_REALIZABLE_NOT_INDEPENDENT_CERTIFICATION',
                             'unrealizable_json': 'UPSTREAM_REPORTED_UNREALIZABLE_NOT_INDEPENDENT_CERTIFICATION'},
            'prior_exposure': 'Entire source inventory and prior solution texts are opened development; no timed runs of this full tool yet',
            'fresh_eligible': 0, 'G0_passed': False, 'G1_admitted': False,
            'headroom_multiplier': None, 'original_results_must_be_preserved': True}


def run(source: Path, output: Path, registration_path: Path):
    contract_bytes = registration_path.read_bytes()
    contract = json.loads(contract_bytes)
    assert contract == registration(source), 'registration/source mismatch'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip() == PIN
    assert not output.exists(), 'first result destination already exists'
    output.mkdir(parents=True)
    (output / 'preregister.json').write_bytes(contract_bytes)
    start = time.perf_counter()
    binary = source / '_build/default/bin/Synduce.exe'
    before = {'binary_sha256': sha(binary),
              'cpu': Path('/proc/cpuinfo').read_text(),
              'kernel': subprocess.check_output(['uname','-a'],text=True),
              'z3': subprocess.check_output(['z3','--version'],text=True),
              'cvc5': subprocess.check_output(['cvc5','--version'],text=True),
              'source_commit': PIN, 'gpu_requested': False}
    (output / 'runtime.json').write_text(json.dumps(before,indent=2)+'\n')
    rows = []
    for case_index, case in enumerate(contract['cases']):
        for repeat in range(contract['repetitions']):
            label = f'{case_index:02}-{repeat}'
            command = [str(binary),'--cvc5','--compact','-j',*case['options'],
                       str(source / 'benchmarks' / case['path'])]
            t = time.perf_counter()
            child = subprocess.Popen(command,cwd=source,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                     start_new_session=True)
            timed_out = False
            try:
                out, err = child.communicate(timeout=contract['external_timeout_seconds'])
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(child.pid,signal.SIGKILL)
                out, err = child.communicate()
            seconds = time.perf_counter() - t
            (output / (label+'.stdout')).write_bytes(out)
            (output / (label+'.stderr')).write_bytes(err)
            decoded = None
            try:
                decoded = json.loads(out)
            except (ValueError, UnicodeDecodeError):
                pass
            if timed_out:
                status = 'NOT_SOLVED_EXTERNAL_TIMEOUT'
            elif child.returncode:
                status = 'EXECUTION_ERROR_NOT_EVALUATED'
            elif not isinstance(decoded,dict):
                status = 'NO_VALID_UPSTREAM_RESULT'
            elif decoded.get('failure'):
                status = 'UPSTREAM_REPORTED_FAILURE'
            elif decoded.get('unrealizable') is True:
                status = 'UPSTREAM_REPORTED_UNREALIZABLE'
            elif isinstance(decoded.get('solution'),str):
                status = 'UPSTREAM_REPORTED_REALIZABLE'
            else:
                status = 'UNCLASSIFIED_UPSTREAM_JSON'
            row = {'label':label,'case_index':case_index,'path':case['path'],'repeat':repeat,
                   'command':command,'seconds':seconds,'timeout':timed_out,'exit_code':child.returncode,
                   'status':status,'upstream_result':decoded,
                   'stdout_sha256':hashlib.sha256(out).hexdigest(),
                   'stderr_sha256':hashlib.sha256(err).hexdigest(),
                   'independently_certified_original_task':False}
            rows.append(row)
            (output / 'observations.json').write_text(json.dumps(rows,indent=2)+'\n')
            print(json.dumps({k:row[k] for k in ['label','path','seconds','status']}),flush=True)
    report = {'experiment_id':contract['experiment_id'],'status':'COMPLETE_UPSTREAM_INTEGRATION_ONLY',
              'workers':len(rows),'cases':len(contract['cases']),
              'status_counts':{status:sum(r['status']==status for r in rows) for status in sorted({r['status'] for r in rows})},
              'whole_seconds':time.perf_counter()-start,
              'registration_sha256':hashlib.sha256(contract_bytes).hexdigest(),
              'runtime':before,'G0_passed':False,'G1_admitted':False,
              'learning_performed':False,'fresh_eligible':0}
    (output / 'report.json').write_text(json.dumps(report,indent=2)+'\n')
    manifest = {path.name:sha(path) for path in output.iterdir() if path.is_file()}
    (output / 'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'runtime'}),flush=True)
