"""Freeze/replay all opened public folds with a stronger native decoder control.

This is engineering, never a new independent capability or headroom experiment.
Old reports, first failures, source protocols and native rights stay unchanged.
"""
from collections import Counter
from pathlib import Path
import hashlib,itertools,json,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from neumann1.recursive_decoder_baseline import propose
from neumann1.recursive_summary import identity,CertifiedSummary,reference
from neumann1.recursive_summary_data import problem_view
from neumann1.structural_data_rights import DataUseError
from neumann1.source_bound_recursive import source_binding,certify_source_summary
from neumann1.source_bound_ocaml import emit
from experiments.recursive_summary_replay import independent_obligations,eval_program
from experiments.synduce_full_baseline_audit import independent_fold,shaped

SOURCES=['neumann1/recursive_decoder_baseline.py','neumann1/recursive_summary.py',
 'neumann1/recursive_library_baseline.py','neumann1/finite_response_baseline.py',
 'neumann1/recursive_summary_data.py','neumann1/structural_data_rights.py',
 'neumann1/source_bound_recursive.py','neumann1/source_bound_ocaml.py',
 'neumann1/typed_fold_projection.py','neumann1/recursive_dag.py',
 'experiments/symbolic_decoder_portfolio.py','experiments/recursive_summary_replay.py',
 'experiments/synduce_full_baseline_audit.py']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def save(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def freeze(opened,intake,preparation):
    assert not preparation.exists();preparation.mkdir(parents=True)
    contract={'experiment_id':'SYMBOLIC_DECODER_PORTFOLIO_ENGINEERING_V1',
      'kind':'opened known-algebra symbolic generation and source binding;not learned NEUMANN/G0/G1',
      'opened_manifest_sha256':sha(opened/'manifest.json'),
      'intake_manifest_sha256':sha(intake/'manifest.json'),'intake_archive_sha256':sha(intake/'upstream.zip'),
      'selection':'all27 already opened typed public ASTs ascending identity;then all564 original benchmark source views;unsupported retained',
      'prior_exposure':'all27 typed projections already opened;seven unresolved ASTs used developer preflight;both original and repaired preflights retained;15 soundness/counterexample unit tests before freeze',
      'native':'known algebra closed projections,input maps,sign/permutation,40 trace decoder proposals,direct products<=8 states;no task-name lookup or Oracle',
      'limits':{'max_unifications':20000,'max_pool':24,'max_checks':24},
      'sufficient_checks':'same9 universal CVC5 conditions;independent Z3 constructed formula and saved CVC5 query,timeout2000ms',
      'numeric':{'alphabet':[-2,0,3],'max_length':4,'shapes':['LEFT','RIGHT','BALANCED']},
      'remote_numeric':'same source-bound emitter Boolean alphabet0/1 and Int[-2,0,3],length0..4,3 shapes;added or changed internal state separately reported',
      'source_bound_scope':'strict pure mathematical OCaml fragment;free-word converter order plus lexicographic termination;not full attributes/modules/effects/machine-int theorem',
      'new_representation_generation_is_learning':False,'official_benchmark_score':False,
      'G0_passed':False,'G1_admitted':False,'G2_admitted':False,'fresh_eligible':0,'learning_performed':False,
      'sources':{n:sha(ROOT/n) for n in SOURCES}}
    save(preparation/'preregister.json',contract)
    for n in SOURCES:
        path=preparation/'source'/n;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/n).read_bytes())
    save(preparation/'freeze.json',{'registration_sha256':sha(preparation/'preregister.json')})
    print(sha(preparation/'preregister.json'))


def unroll(proposal,tree):
    if tree[0]=='nil':return list(proposal['empty'])
    if tree[0]=='single':return eval_program(proposal['step'],[tree[1]]+proposal['empty'])
    return eval_program(proposal['merge'],unroll(proposal,tree[1])+unroll(proposal,tree[2]))


def run(opened,intake,preparation,output):
    import z3
    contract=read(preparation/'preregister.json')
    assert sha(preparation/'preregister.json')==read(preparation/'freeze.json')['registration_sha256']
    assert all(sha(ROOT/n)==sha(preparation/'source'/n)==h for n,h in contract['sources'].items())
    for path,pin in [(opened/'manifest.json',contract['opened_manifest_sha256']),
       (intake/'manifest.json',contract['intake_manifest_sha256']),(intake/'upstream.zip',contract['intake_archive_sha256'])]:assert sha(path)==pin
    for name,pin in read(opened/'manifest.json').items():assert sha(opened/name)==pin
    assert not output.exists();output.mkdir(parents=True);start=time.perf_counter()
    (output/'preregister.json').write_bytes((preparation/'preregister.json').read_bytes())
    registry=read(opened/'registry.json');native={};observations=[];proofs=0;saved_proofs=0;numeric=0;denials=0
    sequences=[list(xs) for n in range(5) for xs in itertools.product([-2,0,3],repeat=n)]
    for key,asset in sorted(registry['public'].items()):
        public=problem_view(opened,asset);assert identity(public)==key
        for purpose in ['train','fresh_eval']:
            try:problem_view(opened,asset,purpose)
            except DataUseError:denials+=1
            else:raise AssertionError('Opened data cannot acquire new rights')
        save(output/'public'/(key+'.json'),public)
        found=propose(public,**contract['limits'],checkpoint=lambda r:save(output/'progress'/(key+'.json'),r))
        save(output/'native'/(key+'.json'),found);native[key]=found
        row={'public_AST_sha256':key,'status':found['status'],'accepted':found['accepted'],
             'decoder_candidates':found['decoder_candidates'],'unifications':found['unifications']}
        if found['accepted']:
            for name,theorem in independent_obligations(public,found['proposal']).items():
                solver=z3.Solver();solver.set(timeout=2000);solver.add(z3.Not(theorem));assert solver.check()==z3.unsat,(key,name);proofs+=1
            for lemma in found['certificate']['obligations']:
                solver=z3.Solver();solver.set(timeout=2000);solver.from_string(lemma['smt2']);assert solver.check()==z3.unsat;saved_proofs+=1
            engine=CertifiedSummary(public,found['proposal'])
            for values in sequences:
                expected=independent_fold(public,values);assert reference(public,values)==expected
                for shape in contract['numeric']['shapes']:
                    assert engine.run(shaped(values,shape))==expected;numeric+=1
        observations.append(row);save(output/'observations.json',observations)
        print(key[:8],found['status'],flush=True)
    source_rows=[];cases=[];expected={};termination=0;source_numeric=0
    for asset in read(intake/'manifest.json')['files']:
        source=intake/'upstream'/asset['local_path'];assert sha(source)==asset['sha256']
        if not asset['path'].startswith('benchmarks/') or not asset['path'].endswith(('.ml','.pmrs')):continue
        row={'source':asset,'role':'OPENED_DEVELOPMENT','fresh_eligible':False}
        try:binding=source_binding(source.read_text(encoding='utf-8'))
        except ValueError as error:
            row.update(status='UNSUPPORTED_SOURCE_PROTOCOL_NO_CLAIM',reason=str(error));source_rows.append(row);continue
        public=binding['projection']['public'];key=identity(public)
        label=f'{len(source_rows):03}-{asset["sha256"][:16]}'
        save(output/'bindings'/(label+'.json'),binding)
        for lemma in binding['flatten_proof']['proof_records']:
            solver=z3.Solver();solver.set(timeout=2000);solver.from_string(lemma['termination_smt2']);assert solver.check()==z3.unsat;termination+=1
        row.update(status='SOURCE_PROTOCOL_BOUND_NO_SUMMARY',public_AST_sha256=key,label=label)
        found=native.get(key)
        if found is None or not found['accepted']:source_rows.append(row);continue
        certificate=certify_source_summary(source.read_text(encoding='utf-8'),found['proposal'])
        save(output/'certificates'/(label+'.json'),certificate)
        row['native_status']=certificate['status']
        if not certificate['accepted']:source_rows.append(row);continue
        row.update(status='SOURCE_GOAL_CERTIFIED_WITH_NATIVE_SUMMARY',original_hole_skeleton_implementable=certificate['original_hole_skeleton_implementable'])
        ocaml,spec=emit(binding,found['proposal']);path=output/'ocaml'/(label+'.ml');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(ocaml,encoding='utf-8')
        rows=[]
        for length in range(5):
            for code in range(len(spec['alphabet'])**length):
                values=[spec['alphabet'][(code//len(spec['alphabet'])**i)%len(spec['alphabet'])] for i in range(length)]
                target=independent_fold(public,values)
                for shape,shape_name in enumerate(['RIGHT','LEFT','BALANCED']):
                    assert eval_program(found['proposal']['decode'],unroll(found['proposal'],shaped(values,shape_name)))==target
                    rows.append({'length':length,'code':code,'shape':shape,'values':values,'expected':target});source_numeric+=1
        assert len(rows)==spec['rows'];expected[label]=rows
        cases.append({'label':label,'source':asset,'public_AST_sha256':key,'ocaml_path':'ocaml/'+label+'.ml',
           'ocaml_sha256':sha(path),'specification':spec,'original_hole_skeleton_implementable':certificate['original_hole_skeleton_implementable']})
        source_rows.append(row)
    save(output/'source-inventory.json',source_rows);save(output/'cases.json',cases);save(output/'expected.json',expected)
    remote={'experiment_id':contract['experiment_id'],'kind':'frozen actual OCaml finite replay;no new capability/cost evidence',
      'registration_sha256':sha(preparation/'preregister.json'),'cases':cases,'compile_timeout_seconds':60,'run_timeout_seconds':30,
      'opam_switch':'neumann','files':{c['ocaml_path']:c['ocaml_sha256'] for c in cases},'G1_admitted':False,'fresh_eligible':0}
    save(output/'remote-contract.json',remote);archive=output/'OCAML_SYMBOLIC_DECODER_REPLAY_INPUTS.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for name in ['remote-contract.json',*remote['files']]:z.write(output/name,name)
    report={'experiment_id':contract['experiment_id'],'status':'COMPLETE_OPENED_NATIVE_ENGINEERING',
      'distinct_opened_public_ASTs':len(native),'certified_opened_public_ASTs':sum(r['accepted'] for r in native.values()),
      'native_status_counts':dict(Counter(r['status'] for r in native.values())),
      'independent_Z3_conditions':proofs,'saved_CVC5_conditions_replayed_in_Z3':saved_proofs,
      'independent_numeric_tree_rows':numeric,'data_rights_denials':denials,
      'source_views':len(source_rows),'source_protocol_bound':sum(r['status']!='UNSUPPORTED_SOURCE_PROTOCOL_NO_CLAIM' for r in source_rows),
      'certified_source_goal_views':len(cases),'distinct_source_byte_hashes':len({c['source']['sha256'] for c in cases}),
      'distinct_source_bound_public_ASTs':len({c['public_AST_sha256'] for c in cases}),
      'original_hole_skeleton_implementable':sum(c['original_hole_skeleton_implementable'] for c in cases),
      'requires_added_or_changed_internal_state':sum(not c['original_hole_skeleton_implementable'] for c in cases),
      'Z3_termination_conditions':termination,'independent_source_numeric_rows':source_numeric,
      'source_status_counts':dict(Counter(r['status'] for r in source_rows)),
      'remote_replay_status':'PREPARED_NOT_YET_EXECUTED','remote_input_archive_sha256':sha(archive),
      'whole_engineering_seconds':time.perf_counter()-start,'performance_headroom_claim':False,
      'official_benchmark_score':False,'G0_passed':False,'G1_admitted':False,'G2_admitted':False,
      'fresh_eligible':0,'learning_performed':False}
    save(output/'report.json',report);save(output/'manifest.json',{str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file()})
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    mode,*args=sys.argv[1:]
    (freeze if mode=='freeze' else run)(*(Path(p) for p in args))
