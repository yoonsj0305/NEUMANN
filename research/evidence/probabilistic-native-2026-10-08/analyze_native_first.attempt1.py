"""Independent receipt/hash replay and matched cost analysis; zero solver calls."""
from collections import Counter
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import statistics
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
sys.set_int_max_str_digits(100_000)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_and_extract():
    archive = ROOT/'PROBABILISTIC_NATIVE_FIRST.zip'
    output = ROOT/'native-first-export'
    output.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        assert len(names) == len(set(names))
        manifest = json.loads(bundle.read('export-manifest-first.json'))
        entries = {row['name']: row for row in manifest['files']}
        assert set(names) == set(entries) | {'export-manifest-first.json'}
        for name in names:
            path = (output/name).resolve()
            assert path.is_relative_to(output.resolve()), name
            data = bundle.read(name)
            if name in entries:
                assert len(data) == entries[name]['bytes'] and sha(data) == entries[name]['sha256'], name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(data)
    return output, {'archive_sha256': sha(archive.read_bytes()), 'bytes': archive.stat().st_size,
                    'entries': len(names), 'manifest_verified_files': len(entries)}


def analyze(output, archive_receipt):
    contract = json.loads((output/'probabilistic-native.preregister.json').read_bytes())
    assert sha((output/'probabilistic_native_diagnostic.py').read_bytes()) == contract['runner_sha256']
    assert sha((output/'source-cases-parent-first.json').read_bytes()) == contract['parent_cases_sha256']
    assert sha((output/'native-sources-first.json').read_bytes()) == contract['native_source_manifest_sha256']
    parent = json.loads((output/'source-cases-parent-first.json').read_bytes())
    cases = {row['case_id']: row for row in parent['cases']}
    report = json.loads((output/'native-first/report-first.json').read_bytes())
    rows = report['rows']
    manifest = json.loads((output/'native-sources-first.json').read_bytes())
    for case in cases.values():
        assert sha((output/'inputs'/case['family']/case['file']).read_bytes()) == case['file_sha256']
    for row in manifest:
        for kind in ['prism','properties']:
            if row[kind]:
                entry = row[kind]
                assert sha((output/'native-inputs'/row['family']/entry['name']).read_bytes()) == entry['sha256']
    jobs = list(sorted((output/'native-first').glob('*/parent-receipt-first.json')))
    assert len(jobs) == report['executed_jobs']
    goal_counts = Counter(); errors = Counter(); process_failures = []
    for path, row in zip(jobs, rows):
        assert json.loads(path.read_bytes()) == row
        request = json.loads((path.parent/'request-first.json').read_bytes())
        assert set(request['case']) == {'case_id','family','file','goal','parameters','file_sha256','goal_expression'}
        for attempt in row['attempts']:
            raw = (path.parent/f'repeat-{attempt["repeat"]}.json').read_bytes()
            assert sha(raw) == attempt['raw_receipt_sha256']
            original = json.loads(raw)
            for key, value in original.items():
                assert attempt[key] == value
            if attempt['status'] == 'OUTPUT_OBSERVED_NOT_YET_JUDGED':
                reference = Fraction(cases[row['case_id']]['expected_exact'])
                assert Fraction(attempt['original_goal_output']) == reference
                assert all(Fraction(check['output']) == reference for check in attempt.get('compiled_reuse_checks', []))
                assert attempt['independent_reference_verdict'] == 'PASS'
            else:
                assert attempt['independent_reference_verdict'] == 'NOT_VERIFIED'
                errors[(attempt.get('error_type'),attempt.get('error'))] += 1
            goal_counts[attempt['independent_reference_verdict']] += 1
        if row['status'] == 'PROCESS_FAILED':
            process_failures.append({'job_no': row['job_no'], 'case_id': row['case_id'], 'format':row['format'], 'route':row['route'],
                                     'returncode':row['returncode'], 'stderr': (path.parent/'stderr-first.log').read_text(errors='replace')[-3000:]})
    matched = []
    cells = []
    for case_id, case in cases.items():
        valid = [row for row in rows if row['case_id'] == case_id and row['status'] == 'FINISHED' and
                 len(row['attempts']) == 4 and all(a['independent_reference_verdict'] == 'PASS' for a in row['attempts'])]
        observed = [a for row in rows if row['case_id'] == case_id for a in row['attempts'] if a['independent_reference_verdict']=='PASS']
        cell = {'case_id': case_id, 'family': case['family'], 'observed_exact_outputs':len(observed),
                'fully_verified_native_paths':len(valid), 'status':'COMPLETE_PATH_AVAILABLE' if valid else 'INCOMPLETE',
                'native_cold_seconds':None, 'native_resident_fresh_seconds':None,
                'free_optimistic_cold_seconds':None, 'free_optimistic_resident_seconds':None,
                'native_over_free_cold':None,'native_over_free_resident':None,
                'native_over_free_compiled_reuse':None,
                'max_state_reduction':None,'max_transition_reduction':None}
        if valid:
            warm = lambda row: statistics.median(a['request_seconds'] for a in row['attempts'][1:])
            cold = lambda row: row['attempts'][0]['cold_first_output_seconds']
            best_warm = min(valid, key=warm); best_cold = min(valid, key=cold)
            cell.update(native_cold_seconds=cold(best_cold),native_resident_fresh_seconds=warm(best_warm),
                        native_cold_path=f'{best_cold["format"]}/{best_cold["route"]}',
                        native_resident_path=f'{best_warm["format"]}/{best_warm["route"]}')
            free = [row for row in valid if 'bisim' in row['route']]
            if free:
                floor_warm = lambda row: statistics.median(a['stage_seconds']['parse_bind_goal']+a['stage_seconds']['execute_restore'] for a in row['attempts'][1:])
                floor_cold = lambda row: row['attempts'][0]['startup_from_parent_seconds']+row['attempts'][0]['stage_seconds']['parse_bind_goal']+row['attempts'][0]['stage_seconds']['execute_restore']
                fw,fc = min(free,key=floor_warm), min(free,key=floor_cold)
                cell.update(free_optimistic_cold_seconds=floor_cold(fc),free_optimistic_resident_seconds=floor_warm(fw),
                            native_over_free_cold=cell['native_cold_seconds']/floor_cold(fc),
                            native_over_free_resident=cell['native_resident_fresh_seconds']/floor_warm(fw),
                            free_cold_path=f'{fc["format"]}/{fc["route"]}',free_resident_path=f'{fw["format"]}/{fw["route"]}',
                            max_state_reduction=max(a['original_states']/a['executed_states'] for row in free for a in row['attempts']),
                            max_transition_reduction=max(a['original_transitions']/a['executed_transitions'] for row in free for a in row['attempts']))
                for row in free:
                    checks = [check for a in row['attempts'] for check in a['compiled_reuse_checks'] if not check['warmup']]
                    native = statistics.median(c['seconds'] for c in checks if c['arm']=='NATIVE_COMPILED_REUSE')
                    supplied = statistics.median(c['seconds'] for c in checks if c['arm']=='FREE_VALID_PERSPECTIVE_LOWER_BOUND')
                    matched.append({'case_id':case_id,'format':row['format'],'route':row['route'],
                                    'native_seconds':native,'free_seconds':supplied,'ratio':native/supplied})
                cell['native_over_free_compiled_reuse'] = statistics.geometric_mean(r['ratio'] for r in matched if r['case_id']==case_id)
        cells.append(cell)
    families = {}
    for name in sorted({case['family'] for case in cases.values()}):
        group = [cell for cell in cells if cell['family']==name]
        available = [cell for cell in group if cell['native_over_free_resident'] is not None]
        two_bins = len(group)==2 and all(cell in available for cell in group)
        families[name] = {'requests':len(group),'available_comparable_requests':len(available),
                          'resident_optimistic_geomean':statistics.geometric_mean(c['native_over_free_resident'] for c in available) if available else None,
                          'two_registered_bins_with_verified_paths':two_bins,
                          'screening':'NO_REGISTERED_FAMILY_PASS' if not two_bins else ('POTENTIAL_ONLY_REQUIRES_MISSING_COMPARATOR_AND_CERTIFICATE' if statistics.geometric_mean(c['native_over_free_resident'] for c in available)>=10 else 'NO_TENFOLD_OPTIMISTIC_HEADROOM_IN_TESTED_PATHS')}
    result = {'kind':'INDEPENDENT_FIRST_RECEIPT_REPLAY_AND_POSTHOC_COST_ANALYSIS',
              'archive':archive_receipt,'contract_sha256':sha((output/'probabilistic-native.preregister.json').read_bytes()),
              'scheduled_jobs':report['scheduled_jobs'],'executed_jobs':report['executed_jobs'],
              'job_statuses':dict(Counter(row['status'] for row in rows)), 'goal_verdicts':dict(goal_counts),
              'fully_verified_jobs':sum(cell['fully_verified_native_paths'] for cell in cells),
              'independent_case_requests':len(cases),'model_families':len(families),'unique_JANI_files':len({(c['family'],c['file']) for c in cases.values()}),
              'total_parent_wall_seconds':report['total_parent_wall_seconds'],
              'parent_reference_audit_seconds':sum(a['reference_judge_seconds'] for row in rows for a in row['attempts']),
              'cohort_status':'INCOMPLETE' if len(jobs)<report['scheduled_jobs'] or any(row['status']!='FINISHED' or len(row['attempts'])!=4 or any(a['independent_reference_verdict']!='PASS' for a in row['attempts']) for row in rows) else 'COMPLETE',
              'errors':[{'error_type':kind,'message':msg,'count':count} for (kind,msg),count in errors.items()],
              'process_failures':process_failures,'families':families,'cells':cells,'compiled_reuse_controls':matched,
              'new_solver_calls_in_analysis':0,'new_model_forwards':0,'decision':'HOLD_LEARNING',
              'cost_scope':'Optimistic free quotient floors retain original parse/bind/hash and exact solve/restore; reference judgement is diagnostic audit cost, not a deployable per-request verifier; omit quotient construction, delivery and independent certificate costs. Cold floor charges measured process startup. Native receives the same compilation/reuse rights.',
              'harness_limit':'Parent subprocess.wait polling quantizes job wall; use worker perf_counter_ns for internal latency. Timed-out jobs have no receipt for unfinished repeat, so missing stage costs are UNKNOWN.',
              'strong_comparator_gap':'Herman15 has a published exact analytic formula; Storm portfolio is not strongest native there. Some native routes failed or were not verified, so all strongest-comparator claims are qualified.',
              'unknown_axes':['Oracle delivery','independent quotient proof acquisition','energy','FLOPs','money','training','full lifecycle investment'],
              'statistical_scope':'Three repeats and opened requests are diagnostic, not independent broad generalization.'}
    with (ROOT/'native-analysis-first.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2,allow_nan=False)
    fields=list(dict.fromkeys(k for row in cells for k in row))
    with (ROOT/'native-analysis-first.csv').open('x',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(cells)
    return result


if __name__=='__main__':
    output,receipt=verify_and_extract()
    result=analyze(output,receipt)
    print(json.dumps({k:result[k] for k in ['archive','job_statuses','goal_verdicts','fully_verified_jobs','total_parent_wall_seconds','cohort_status','families','errors','decision']},indent=2))
