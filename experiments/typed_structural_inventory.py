"""One registered opened-source portfolio integration, never a G0 verdict."""
from collections import Counter,defaultdict
from pathlib import Path
import hashlib,itertools,json,sys,time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from neumann1.typed_fold_projection import project
from neumann1.recursive_library_baseline import propose as library
from neumann1.finite_response_baseline import propose as finite_response
from neumann1.recursive_summary import check_summary,CertifiedSummary,identity,reference
from neumann1.recursive_summary_data import problem_view
from neumann1.structural_data_rights import DataUseError,authorize
from experiments.recursive_summary_replay import independent_obligations
from experiments.synduce_full_baseline_audit import shaped,independent_fold


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def read(path):return json.loads(path.read_text(encoding='utf-8'))


SOURCES=['neumann1/typed_fold_projection.py','neumann1/recursive_library_baseline.py',
         'neumann1/finite_response_baseline.py','neumann1/recursive_summary.py',
         'neumann1/recursive_summary_data.py','neumann1/structural_data_rights.py',
         'neumann1/synduce_reference.py','experiments/typed_structural_inventory.py',
         'experiments/recursive_summary_replay.py','experiments/synduce_full_baseline_audit.py']


def register(intake, preparation):
    assert not preparation.exists();preparation.mkdir(parents=True)
    contract={'experiment_id':'TYPED_RECURSIVE_PORTFOLIO_INTEGRATION_V1',
              'kind':'OPENED_DEVELOPMENT_ENGINEERING_NOT_CAPABILITY_OR_COST_HEADROOM',
              'intake_manifest_sha256':sha(intake/'manifest.json'),
              'archive_sha256':sha(intake/'upstream.zip'),
              'sources':{name:sha(ROOT/name) for name in SOURCES},
              'execution_order':'all pinned benchmark source files; distinct public AST hash ascending; library then finite response',
              'selection':'all supported typed projections; no choosing only positive cases',
              'checker':'CVC5 nine conditions default 2000ms/200000 resource per condition; independent Z3 same theorem 2000ms',
              'numeric_alphabet':[-2,0,3],'max_length':4,'shapes':['LEFT','RIGHT','BALANCED'],
              'prior_exposure':'source and solution inventories, 27 AST preview plus unit fixtures already opened; current parser/native design used these development previews',
              'AST_identity_is_structural_independence_proof':False,
              'original_repr_target_attributes_machine_overflow_checked':False,
              'G0_passed':False,'G1_admitted':False,'fresh_eligible':0,'learning_performed':False}
    save(preparation/'preregister.json',contract)
    for name in SOURCES:
        dest=preparation/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes())
    save(preparation/'freeze.json',{'registration_sha256':sha(preparation/'preregister.json')})
    print(sha(preparation/'preregister.json'))


def run(intake, preparation, output):
    import z3
    contract=read(preparation/'preregister.json')
    assert sha(preparation/'preregister.json')==read(preparation/'freeze.json')['registration_sha256']
    assert all(sha(ROOT/n)==h==sha(preparation/'source'/n) for n,h in contract['sources'].items())
    assert sha(intake/'manifest.json')==contract['intake_manifest_sha256']
    assert sha(intake/'upstream.zip')==contract['archive_sha256']
    assert not output.exists();output.mkdir(parents=True)
    (output/'preregister.json').write_bytes((preparation/'preregister.json').read_bytes())
    start=time.perf_counter();manifest=read(intake/'manifest.json');groups=defaultdict(list);projections={};inventory=[]
    for source in manifest['files']:
        path=intake/'upstream'/source['local_path'];assert sha(path)==source['sha256']
        if not source['path'].startswith('benchmarks/') or not source['path'].endswith(('.ml','.pmrs')):continue
        row={'source':source,'original_protocol_checked':False,'role':'D','fresh_eligible':False}
        try:
            projection=project(path.read_text(encoding='utf-8'));key=identity(projection['public'])
            groups[key].append(row);projections[key]=projection
            row.update(status='SUPPORTED_ADAPTED_TYPED_REFERENCE',projection_sha256=key,
                       reference_function=projection['reference_function'],input_type=projection['input_type'],goal_types=projection['goal_types'])
        except ValueError as error:row.update(status='UNSUPPORTED_NO_CLAIM',reason=str(error))
        inventory.append(row)
    save(output/'inventory.json',inventory)
    registry={'schema':'neumann.opened-typed-recursive-portfolio.v1','public':{},'offline':{}}
    proposals=[];checks=0;proofs=0;numeric=0;denials=0
    sequences=[list(xs) for n in range(contract['max_length']+1) for xs in itertools.product(contract['numeric_alphabet'],repeat=n)]
    for key in sorted(groups):
        public=projections[key]['public'];public_path=output/'public'/(key+'.json');save(public_path,public)
        asset={'role':'D','allowed_use':'opened_development_only','problem_kind':'integer_list_right_fold',
               'path':str(public_path.relative_to(output)),'sha256':sha(public_path),
               'equivalence_group':'exact-adapted-AST/'+key,'historically_opened':True,'fresh_eligible':False,
               'source_study':contract['experiment_id'],'source_originals':[g['source'] for g in groups[key]],
               'projection_semantics':'adapted mathematical typed Nil/Cons reference; no original protocol or independence claim'}
        registry['public'][key]=asset
        assert problem_view(output,asset)==public
        for purpose in ['train','fresh_eval']:
            try:problem_view(output,asset,purpose)
            except DataUseError:denials+=1
            else:raise AssertionError('Opened data authority expanded')
        for route,proposer in [('KNOWN_LIBRARY',library),('GENERATED_FINITE_RESPONSE',finite_response)]:
            before=time.perf_counter();found=proposer(public);generation_seconds=time.perf_counter()-before
            row={'problem':key,'route':route,'generation_seconds':generation_seconds,
                 'cost_scope':'preloaded native proposal diagnostic only; not complete or comparative cost'}
            if found is None:
                row.update(status='ABSTAINED_BOUNDED_NATIVE_GRAMMAR',accepted=False)
                save(output/'native'/route/(key+'.json'),row);proposals.append(row);continue
            cert=check_summary(public,found['proposal']);checks+=len(cert['obligations'])
            row.update(status=cert['status'],accepted=cert['accepted'],native=found,certificate=cert)
            if cert['accepted']:
                for name,theorem in independent_obligations(public,found['proposal']).items():
                    solver=z3.Solver();solver.set(timeout=2000);solver.add(z3.Not(theorem))
                    assert solver.check()==z3.unsat,(key,route,name);proofs+=1
                engine=CertifiedSummary(public,found['proposal'])
                for values in sequences:
                    expected=independent_fold(public,values)
                    assert reference(public,values)==expected
                    for shape in contract['shapes']:
                        assert engine.run(shaped(values,shape))==expected;numeric+=1
                o=output/'offline'/(key+'-'+route+'.json');save(o,found)
                oracle={**asset,'role':'O','runtime':False,'path':str(o.relative_to(output)),'sha256':sha(o)}
                registry['offline'][key+'/'+route]=oracle
                try:problem_view(output,oracle)
                except DataUseError:denials+=1
                else:raise AssertionError('Offline proposal entered problem API')
            save(output/'native'/route/(key+'.json'),row);proposals.append(row)
    save(output/'registry.json',registry)
    accepted_keys={r['problem'] for r in proposals if r['accepted']}
    report={'experiment_id':contract['experiment_id'],'status':'COMPLETE_ENGINEERING_PORTFOLIO_ONLY',
            'source_files_hash_checked':len(manifest['files']),'benchmark_sources':len(inventory),
            'supported_source_projections':sum(r['status']=='SUPPORTED_ADAPTED_TYPED_REFERENCE' for r in inventory),
            'distinct_public_ASTs':len(groups),'AST_identity_is_independence_proof':False,
            'native_attempts':len(proposals),'native_status_counts':dict(Counter((r['route']+':'+r['status']) for r in proposals)),
            'certified_public_ASTs':len(accepted_keys),
            'uncertified_ASTs':[{'sha256':key,'sources':[g['source']['path'] for g in groups[key]]} for key in sorted(set(groups)-accepted_keys)],
            'common_checker_conditions_attempted':checks,'independent_Z3_conditions':proofs,
            'numeric_ordered_tree_comparisons':numeric,'rights_denials':denials,
            'whole_engineering_seconds':time.perf_counter()-start,
            'official_benchmark_score':False,'performance_claim':False,
            'fresh_eligible':0,'G0_passed':False,'G1_admitted':False,'learning_performed':False}
    save(output/'report.json',report)
    save(output/'manifest.json',{str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file()})
    print(json.dumps({k:v for k,v in report.items() if k!='uncertified_ASTs'},indent=2))


if __name__=='__main__':
    mode,*args=sys.argv[1:]
    (register if mode=='register' else run)(*(Path(p) for p in args))
