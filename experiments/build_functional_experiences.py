"""D0 source-bound structural experience assets, without training/evaluation activation."""
from pathlib import Path
from collections import Counter
import hashlib,json
from neumann1.functional_source import parse,SourceError
from neumann1.functional_types import TypeChecker
from neumann1.functional_examples import entrypoints
from neumann1.functional_experience_store import ExperienceStore


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def public(source):
    commands=parse(source);checker=TypeChecker(commands);types=checker.check(commands)
    return {'source':source,'commands':commands,'declared_entrypoints':entrypoints(commands),
            'erased_type_signatures':types,'author_sampling_config':[c[1:]for c in commands if c[0]=='config']}


def run(work):
    intake=work/'Continuation/SUFU_SOURCE_FIRST';intake_manifest=json.loads((intake/'manifest.json').read_text());files={f['path']:f for f in intake_manifest['files']}
    native=work/'Continuation/SUFU_NATIVE_FIRST/neumann-sufu/native-suite-first';nr=json.loads((native/'report.json').read_text())
    stress=work/'Continuation/FUNCTIONAL_STRESS_FIRST';sr=json.loads((stress/'report.json').read_text());stress_by={c['index']:c for c in sr['cases_detail']}
    replay=work/'Continuation/SUFU_NATIVE_REPLAYS_FIRST/neumann-resume/sufu-witness-owned-replay/first';rr=json.loads((replay/'report.json').read_text());replay_by={c['index']:c for c in rr['cases']}
    audit=work/'Continuation/SUFU_NATIVE_REPLAYS_AUDIT';ar=json.loads((audit/'report.json').read_text());assert ar['status']=='PASS_ALL_NATIVE_REPLAY_ARTIFACTS_AND_NONERROR_VALUES'
    diffs=json.loads((audit/'native-differences.json').read_text());diff_by={}
    for d in diffs:diff_by.setdefault(d['index'],[]).append(d)
    root=work/'Continuation/FUNCTIONAL_EXPERIENCES_FIRST';root.mkdir();records=[];rights_tests=0
    for c in nr['outcomes']:
        i=c['index'];folder=root/f'{i:03}';folder.mkdir();original=intake/'upstream'/files[c['benchmark']['path']]['local_path'];assert sha(original)==c['benchmark']['sha256']
        payload=public(original.read_text());save(folder/'original.json',payload)
        proposal=native/f'{i:03}'/'optimized.f';assets={}
        def asset(name,role):
            return {'role':role,'path':f'{i:03}/{name}.json','sha256':sha(folder/(name+'.json')),
                    'allowed_use':'opened_development_only','runtime':False if role=='O'else None}
        assets['original']=asset('original','D')
        if proposal.exists():
            text=proposal.read_text();assert sha(proposal)==c['optimized_sha256']
            try:commands=parse(text);types=TypeChecker(commands).check(commands);parse_status='ERASED_TYPES_CHECKED'
            except SourceError as e:commands=None;types=None;parse_status='NOT_VERIFIED: '+str(e)
            save(folder/'proposal.json',{'source':text,'commands':commands,'erased_type_signatures':types,'syntax_status':parse_status,
                                        'upstream_status':c['status'],'broad_typed_domain_refuted':bool(diff_by.get(i)),
                                        'universal_equivalence_proven':False,'origin':'Known SuFu native synthesis; not a learned NEUMANN policy'})
            assets['proposal']=asset('proposal','O')
        fixtures=[]
        for d in diff_by.get(i,[]):
            row=stress_by[i]['rows'][d['row_id']]
            fixtures.append({'entrypoint':row['original_named_entrypoint'],'inputs':row['inputs'],'arguments':row['arguments'],
                             'original_output':d['original'],'proposed_output':d['optimized'],'phase':row['phase'],
                             'native_confirmed':True,'within_author_sample_domain':'NOT_ASSUMED','not_an_official_score_rejudgment':True})
        save(folder/'counterexamples.json',fixtures);assets['counterexamples']=asset('counterexamples','F')
        history={'native_first':c,'stress_status':stress_by[i]['status'],'stress_row_counts':stress_by[i].get('row_counts'),
                 'native_replay':replay_by.get(i),'native_discovery_seconds':c['launch_to_exit_seconds'],
                 'native_discovery_environment':'Kaggle CPU; source/runtime receipts kept separately',
                 'local_stress_seconds_per_case':None,'energy':None,'FLOPs':None,'full_investment_cost':None,
                 'no_addition_of_seconds_from_different_hardware':True,'universal_equivalence_proven':False}
        save(folder/'history.json',history);assets['history']=asset('history','H')
        record={'record_id':'sufu:'+c['benchmark']['sha256'],'source_path':c['benchmark']['path'],
                'original_source_sha256':c['benchmark']['sha256'],'source_artifact_sha256':'0eb8edd69373761be3052a5ab0e838335d75df21f807604907436492bf20878b',
                'equivalence_group':'declared_exact_source_bytes:'+c['benchmark']['sha256'],
                'equivalence_group_does_not_establish_arbitrary_semantic_equivalence':True,
                'evidence_status':'OPENED_DEVELOPMENT','research_exposure':True,'neural_training_performed':False,
                'fresh_eligible':False,'allowed_use':'opened_development_only','native_status':c['status'],
                'confirmed_counterexamples':len(fixtures),'assets':assets}
        records.append(record)
    index={'study':'D0_FUNCTIONAL_STRUCTURAL_EXPERIENCE_ASSETS_V1','records':records,'count':len(records),
           'upstream_commit':'c2b3ff0637460c568b0533f992007278f88d0f55','upstream_first_report_sha256':sha(native/'report.json'),
           'stress_report_sha256':sha(stress/'report.json'),'native_replay_report_sha256':sha(replay/'report.json'),
           'fresh_eligible':0,'training_activated':False,'G0_passed':False,'G1_admitted':False,'G2_admitted':False}
    save(root/'index.json',index);store=ExperienceStore(root,sha(root/'index.json'))
    for r in records:
        assert store.view(r['record_id'],'original','development_problem')['source']
        for field,a in r['assets'].items():
            for purpose in ['train','fresh_evaluation','runtime_oracle']:
                try:store.view(r['record_id'],field,purpose)
                except ValueError:rights_tests+=1
                else:raise AssertionError('Disallowed data purpose accepted')
    report={'status':'PASS_D0_OPENED_FUNCTIONAL_EXPERIENCE_ASSETS','originals':len(records),
            'proposal_assets':sum('proposal'in r['assets']for r in records),'confirmed_counterexample_rows':sum(r['confirmed_counterexamples']for r in records),
            'counterexample_programs':sum(bool(r['confirmed_counterexamples'])for r in records),'loader_denials':rights_tests,
            'historical_native_statuses':dict(Counter(r['native_status']for r in records)),
            'index_sha256':sha(root/'index.json'),'training':False,'fresh_eligible':0,'G0_passed':False,'G1_admitted':False,'G2_admitted':False}
    save(root/'report.json',report);save(root/'manifest.json',{p.relative_to(root).as_posix():sha(p)for p in sorted(root.rglob('*'))if p.is_file()})
    print(json.dumps(report,indent=2))


if __name__=='__main__':run(Path(__file__).resolve().parents[3])
