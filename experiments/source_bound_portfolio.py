"""Opened source-bound engineering and frozen actual OCaml replay preparation."""
from collections import Counter
from pathlib import Path
import hashlib,itertools,json,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from neumann1.source_bound_recursive import source_binding,certify_source_summary
from neumann1.source_bound_ocaml import emit
from neumann1.recursive_library_baseline import propose as library
from neumann1.finite_response_baseline import propose as finite_response
from neumann1.recursive_summary import identity
from experiments.synduce_full_baseline_audit import independent_fold,shaped
from experiments.recursive_summary_replay import eval_program

SOURCES=['neumann1/source_bound_recursive.py','neumann1/source_bound_ocaml.py',
         'neumann1/typed_fold_projection.py','neumann1/recursive_summary.py',
         'neumann1/recursive_library_baseline.py','neumann1/finite_response_baseline.py',
         'experiments/source_bound_portfolio.py','experiments/recursive_summary_replay.py',
         'experiments/synduce_full_baseline_audit.py']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def save(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def freeze(intake,preparation):
    assert not preparation.exists();preparation.mkdir(parents=True)
    contract={'experiment_id':'SOURCE_BOUND_RECURSIVE_ENGINEERING_V1','kind':'opened engineering,not G0/G1/capability/headroom',
              'source_commit':'b5c1d1611d3fbf5d8cdf9a23fde52c2cbba95a89',
              'intake_manifest_sha256':sha(intake/'manifest.json'),'intake_archive_sha256':sha(intake/'upstream.zip'),
              'selection':'all564 pinned benchmark sources;strict direct polymorphic constructor/reference/assertion fragment;unsupported retained',
              'new_protocol':'source assert target=repr@@reference;free-word order proof;lexicographic termination proof;universal generated summary conditions',
              'native':'existing frozen public known library then finite response;no source names/Oracle/learned policy',
              'original_skeleton':'report implementability separately from goal recovery requiring generated added/changed state',
              'numeric':'alllengths0..4;Int heads[-2,0,3],Bool heads[0,1];three actual ordered shapes;allrows retained',
              'OCaml':'exact validated reference and converter bodies plus separate native summary;canonical same constructor ADTs;source holes/attributes removed',
              'remote_environment':'existing Kaggle CPU OCaml5.0.0 opam switch neumann;compile timeout60s,run30s;no GPU',
              'whole_OCaml_workflow_proof':False,'all_machine_integer_equivalence':False,'official_benchmark_score':False,
              'prior_exposure':'typed27AST inventory and source previews used design;26 direct bindings previewed;MSS OCaml363-row preflight plus environment-selection failure/repair before freeze;all opened',
              'G0_passed':False,'G1_admitted':False,'G2_admitted':False,'fresh_eligible':0,'learning_performed':False,
              'sources':{n:sha(ROOT/n) for n in SOURCES}}
    save(preparation/'preregister.json',contract)
    for n in SOURCES:
        dest=preparation/'source'/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/n).read_bytes())
    save(preparation/'freeze.json',{'registration_sha256':sha(preparation/'preregister.json'),'first_run_started':False})
    print(sha(preparation/'preregister.json'))


def interpreted(proposal,tree):
    if tree[0]=='nil':return proposal['empty']
    if tree[0]=='single':return eval_program(proposal['step'],[tree[1]]+proposal['empty'])
    return eval_program(proposal['merge'],interpreted(proposal,tree[1])+interpreted(proposal,tree[2]))


def run(intake,preparation,output):
    import z3
    contract=read(preparation/'preregister.json')
    assert sha(preparation/'preregister.json')==read(preparation/'freeze.json')['registration_sha256']
    assert all(sha(ROOT/n)==sha(preparation/'source'/n)==h for n,h in contract['sources'].items())
    assert sha(intake/'manifest.json')==contract['intake_manifest_sha256'] and sha(intake/'upstream.zip')==contract['intake_archive_sha256']
    assert not output.exists();output.mkdir(parents=True)
    (output/'preregister.json').write_bytes((preparation/'preregister.json').read_bytes())
    inventory=[];cases=[];expected={};proofs=0;comparisons=0;start=time.perf_counter()
    manifest=read(intake/'manifest.json')
    for asset in manifest['files']:
        source=intake/'upstream'/asset['local_path'];assert sha(source)==asset['sha256']
        if not asset['path'].startswith('benchmarks/') or not asset['path'].endswith(('.ml','.pmrs')):continue
        row={'source':asset,'role':'OPENED_DEVELOPMENT','fresh_eligible':False}
        try:binding=source_binding(source.read_text(encoding='utf-8'))
        except ValueError as error:
            row.update(status='UNSUPPORTED_SOURCE_PROTOCOL_NO_CLAIM',reason=str(error));inventory.append(row);continue
        public=binding['projection']['public'];key=identity(public);label=asset['sha256'][:16]
        save(output/'bindings'/(label+'.json'),binding)
        for lemma in binding['flatten_proof']['proof_records']:
            solver=z3.Solver();solver.set(timeout=2000);solver.from_string(lemma['termination_smt2'])
            assert solver.check()==z3.unsat;proofs+=1
        row.update(status='SOURCE_PROTOCOL_BOUND_NO_SUMMARY',public_AST_sha256=key,binding='bindings/'+label+'.json')
        found=library(public)
        if found is None:found=finite_response(public)
        if found is None:
            row['native_status']='ABSTAINED_BOUNDED_PUBLIC_GENERATORS';inventory.append(row);continue
        result=certify_source_summary(source.read_text(encoding='utf-8'),found['proposal'])
        save(output/'certificates'/(label+'.json'),result)
        row.update(native_status=result['status'],certificate='certificates/'+label+'.json')
        if not result['accepted']:inventory.append(row);continue
        proposal=found['proposal'];ocaml,spec=emit(binding,proposal)
        row.update(status='SOURCE_GOAL_CERTIFIED_WITH_NATIVE_SUMMARY',
                   original_hole_skeleton_implementable=result['original_hole_skeleton_implementable'])
        path=output/'ocaml'/(label+'.ml');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(ocaml,encoding='utf-8')
        outputs=[]
        for length in range(5):
            for code in range(len(spec['alphabet'])**length):
                values=[spec['alphabet'][(code//(len(spec['alphabet'])**i))%len(spec['alphabet'])] for i in range(length)]
                reference=independent_fold(public,values)
                for shape,shape_name in enumerate(['RIGHT','LEFT','BALANCED']):
                    assert eval_program(proposal['decode'],interpreted(proposal,shaped(values,shape_name)))==reference
                    outputs.append({'length':length,'code':code,'shape':shape,'values':values,'expected':reference});comparisons+=1
        assert len(outputs)==spec['rows']
        expected[label]=outputs
        case={'label':label,'source':asset,'public_AST_sha256':key,'ocaml_path':'ocaml/'+label+'.ml',
              'ocaml_sha256':sha(path),'specification':spec,'proposal':found,
              'original_hole_skeleton_implementable':result['original_hole_skeleton_implementable']}
        cases.append(case);inventory.append(row)
    save(output/'inventory.json',inventory);save(output/'cases.json',cases);save(output/'expected.json',expected)
    remote={'experiment_id':contract['experiment_id'],'kind':'frozen actual OCaml finite replay;not independent capability or cost score',
            'registration_sha256':sha(preparation/'preregister.json'),'cases':[{k:v for k,v in c.items() if k!='proposal'} for c in cases],
            'compile_timeout_seconds':60,'run_timeout_seconds':30,'opam_switch':'neumann',
            'files':{c['ocaml_path']:c['ocaml_sha256'] for c in cases},'G1_admitted':False,'fresh_eligible':0}
    save(output/'remote-contract.json',remote)
    archive=output/'OCAML_SOURCE_BOUND_REPLAY_INPUTS.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for name in ['remote-contract.json']+[c['ocaml_path'] for c in cases]:z.write(output/name,name)
    report={'experiment_id':contract['experiment_id'],'status':'COMPLETE_LOCAL_SOURCE_BOUND_ENGINEERING',
            'all_source_files_hash_checked':len(manifest['files']),'benchmark_sources':len(inventory),
            'source_protocol_bound':sum(r['status']!='UNSUPPORTED_SOURCE_PROTOCOL_NO_CLAIM' for r in inventory),
            'native_certified_source_goals':len(cases),'distinct_certified_public_ASTs':len({c['public_AST_sha256'] for c in cases}),
            'original_hole_skeleton_implementable':sum(c['original_hole_skeleton_implementable'] for c in cases),
            'requires_added_or_changed_internal_state':sum(not c['original_hole_skeleton_implementable'] for c in cases),
            'serialized_termination_queries_in_Z3':proofs,'independent_numeric_control_rows':comparisons,
            'source_status_counts':dict(Counter(r['status'] for r in inventory)),
            'remote_replay_status':'PREPARED_NOT_YET_EXECUTED','remote_input_archive_sha256':sha(archive),'remote_input_archive_bytes':archive.stat().st_size,
            'whole_engineering_seconds':time.perf_counter()-start,'official_benchmark_score':False,'performance_headroom_claim':False,
            'G0_passed':False,'G1_admitted':False,'fresh_eligible':0,'learning_performed':False}
    save(output/'report.json',report);save(output/'manifest.json',{str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file()})
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    mode,*paths=sys.argv[1:]
    (freeze if mode=='freeze' else run)(*(Path(p) for p in paths))
