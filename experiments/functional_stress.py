"""Frozen opened source/transform stress. Every exclusion remains in the report."""
from pathlib import Path
from collections import Counter
import hashlib,json,time
from neumann1.functional_source import parse,execute,SourceError
from neumann1.functional_examples import Sampler,concrete_call,decode,encode,entrypoints
from neumann1.functional_types import TypeChecker,compatible


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'))


def run(work):
    repo=Path(__file__).resolve().parents[1]
    prep=work/'Continuation/FUNCTIONAL_STRESS_PREPARATION'
    contract=json.loads((prep/'registration.json').read_text())
    for name,h in contract['source_pins'].items():assert sha(repo/name)==h
    native=work/'Continuation/SUFU_NATIVE_FIRST/neumann-sufu/native-suite-first'
    assert sha(native/'registration.json')==contract['native_registration_sha256']
    native_manifest=json.loads((native/'manifest.json').read_text())
    for name,h in native_manifest.items():assert sha(native/name)==h
    native_report=json.loads((native/'report.json').read_text())
    assert native_report['status']=='COMPLETED_OPENED_ENGINEERING_ONLY'
    assert native_report['benchmark_count']==290
    intake=work/'Continuation/SUFU_SOURCE_FIRST'
    assert sha(intake/'manifest.json')==contract['source_intake_manifest_sha256']
    intake_files={r['path']:r for r in json.loads((intake/'manifest.json').read_text())['files']}
    target=work/'Continuation/FUNCTIONAL_STRESS_FIRST';assert not target.exists();target.mkdir()
    save(target/'registration.json',contract)
    start=time.perf_counter();cases=[]
    for native_case in native_report['outcomes']:
        benchmark=native_case['benchmark'];folder=target/f"{native_case['index']:03}";folder.mkdir()
        result={'index':native_case['index'],'original_path':benchmark['path'],
                'original_sha256':benchmark['sha256'],'native_status':native_case['status'],
                'native_discovery_seconds':native_case['launch_to_exit_seconds'],
                'native_discovery_environment':'Kaggle CPU; not added to local interpreter elapsed time',
                'fresh_eligible':False,'allowed_use':['development','prior_art_baseline','offline_supervision'],
                'universal_equivalence_proven':False,'rows':[]}
        if native_case['status']!='UPSTREAM_BOUNDED_SUCCESS':
            result['status']='NOT_UPSTREAM_SUCCESS_PRESERVED'
        else:
            original=intake/'upstream'/intake_files[benchmark['path']]['local_path']
            optimized=native/f"{native_case['index']:03}"/'optimized.f'
            assert sha(original)==benchmark['sha256']
            assert sha(optimized)==native_case['optimized_sha256']
            result['optimized_sha256']=sha(optimized)
            try:
                original_commands=parse(original.read_text());transformed_commands=parse(optimized.read_text())
                left=TypeChecker(original_commands);right=TypeChecker(transformed_commands)
                lt=left.check(original_commands);rt=right.check(transformed_commands)
                starts=entrypoints(original_commands)
                original_inputs={c[1]:c[2] for c in original_commands if c[0]=='input'}
                transformed_inputs={c[1]:c[2] for c in transformed_commands if c[0]=='input'}
                assert original_inputs.keys()==transformed_inputs.keys(),'Global input interface changed'
                assert all(compatible(t,transformed_inputs[n],left,right) for n,t in original_inputs.items()),'Input datatype structure changed'
                assert all(n in rt and compatible(lt[n],rt[n],left,right) for n in starts),'Entrypoint type structure changed'
                result['status']='ERASED_PUBLIC_SIGNATURES_MATCH'
                for phase_id,phase in enumerate(contract['phases']):
                    sampler=Sampler(original_commands,int(benchmark['sha256'][:16],16)+phase_id,
                                    tuple(phase['numbers']),contract['max_nodes_per_argument'],phase['shape'])
                    for index in range(phase['count']):
                        depth=phase['depths'][index%len(phase['depths'])]
                        row={'phase':phase['name'],'index':index,'depth':depth}
                        try:
                            witness=concrete_call(original_commands,sampler,depth,contract['node_work_per_call'],starts[index%len(starts)])
                            row.update(witness)
                            actual=encode(execute(transformed_commands,[decode(v) for v in witness['arguments']],
                                    {k:decode(v) for k,v in witness['inputs'].items()},
                                    name=witness['original_named_entrypoint'],budget=contract['node_work_per_call'],signed_bits=32))
                            row['transformed_output']=actual
                            row['status']='CONCRETE_MATCH' if canonical(actual)==canonical(witness['original_output']) else 'CONCRETE_COUNTEREXAMPLE'
                        except (SourceError,RecursionError) as error:
                            row['status']='NOT_EVALUATED';row['reason']=type(error).__name__+': '+str(error)
                        result['rows'].append(row)
                result['row_counts']=dict(Counter(r['status'] for r in result['rows']))
                result['status']=('CONCRETE_COUNTEREXAMPLE_FOUND' if result['row_counts'].get('CONCRETE_COUNTEREXAMPLE')
                                  else 'PARTIALLY_CHECKED_CONCRETE_ONLY' if result['row_counts'].get('NOT_EVALUATED')
                                  else 'ALL_REGISTERED_CONCRETE_MATCH_ONLY')
            except (SourceError,AssertionError,RecursionError) as error:
                result['status']='NOT_VERIFIED_INTERFACE_OR_SYNTAX';result['reason']=str(error)
        save(folder/'record.json',result);cases.append(result)
    report={'study':contract['study'],'cases':len(cases),
            'counts':dict(Counter(c['status'] for c in cases)),
            'row_counts':dict(Counter(r['status'] for c in cases for r in c['rows'])),
            'local_interpreter_study_seconds':time.perf_counter()-start,
            'universal_equivalence_proven':False,'official_score':False,'cost_advantage_established':False,
            'fresh_eligible':0,'learning_performed':False,'G0_passed':False,'G1_admitted':False,'G2_admitted':False,
            'native_report_sha256':sha(native/'report.json'),'cases_detail':cases}
    save(target/'report.json',report)
    save(target/'manifest.json',{p.relative_to(target).as_posix():sha(p) for p in sorted(target.rglob('*')) if p.is_file()})
    print(json.dumps({k:v for k,v in report.items() if k!='cases_detail'},indent=2))


if __name__=='__main__':run(Path(__file__).resolve().parents[3])
