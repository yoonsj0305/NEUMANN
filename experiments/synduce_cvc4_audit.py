"""Independent first-file integrity and common adapted-kernel checks, CVC4."""
from pathlib import Path
from collections import Counter
import itertools,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.synduce_full_baseline_audit import (sha,read,save,independently_execute,
    independent_fold,shaped,eval_z3)
from experiments.recursive_summary_replay import independent_obligations,mathematical_reference
from neumann1.typed_fold_projection import project
from neumann1.synduce_solution import certify_solution


def audit(first,intake,preparation,output):
    import z3
    assert not output.exists();output.mkdir(parents=True)
    a=first/'NEUMANN_FULL_SYNDUCE_CVC4_FIRST_RECORDS.zip'
    assert sha(a)=='a26ee94e3b34d635923f8d0488f3023b1980112716bc08037e9970c447d1b5cd'
    with zipfile.ZipFile(a) as zz:
        assert zz.testzip() is None
        for name in zz.namelist():
            assert '\\' not in name and ':' not in name
            target=first/'extracted'/name
            assert target.resolve().is_relative_to((first/'extracted').resolve())
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():assert target.read_bytes()==zz.read(name)
            else:target.write_bytes(zz.read(name))
        archive_files=len(zz.namelist())
    p=first/'extracted/baseline-cvc4-first';manifest=read(p/'manifest.json')
    assert all(sha(p/name)==h for name,h in manifest.items())
    freeze=read(preparation/'freeze.json')
    for name,h in freeze.items():assert sha(preparation/name)==h==sha(first/'extracted/frozen-cvc4-code'/name)
    assert sha(p/'preregister.json')==freeze['preregister.json']=='2907cdc173b12b1ec6ce75c5c7b9f80f0529d018a3a3e24a9abf13fdc9614371'
    c=read(p/'preregister.json');r=read(p/'report.json');rows=read(p/'observations.json');counts=Counter()
    original=read(first.parent/'SYNDuce_FULL_BASELINE_FIRST/extracted/baseline-first/report.json')
    assert r['runtime']['binary_sha256']==original['runtime']['binary_sha256']
    assert r['runtime']['cpu']==original['runtime']['cpu']
    assert r['registration_sha256']==freeze['preregister.json'] and len(rows)==87
    sources={row['path']:row for row in read(intake/'manifest.json')['files']}
    assert [(row['case_index'],row['repeat']) for row in rows]==[(i,j) for i in range(29) for j in range(3)]
    certified=[];excluded=[];proofs=0;serialized=0;numeric=0
    sequences=[list(xs) for n in range(5) for xs in itertools.product([-2,0,3],repeat=n)]+[[10**80,-10**80,3],[-10**90,5,10**90]]
    for row in rows:
        case=c['cases'][row['case_index']]
        assert row['path']==case['path'] and row['label']==f'{row["case_index"]:02}-{row["repeat"]}'
        assert '--cvc4' in row['command'] and row['command'][4:-1]==case['options']
        s=sources['benchmarks/'+row['path']];path=intake/'upstream'/s['local_path']
        assert sha(path)==s['sha256']==case['source_sha256']
        stdout,stderr=p/(row['label']+'.stdout'),p/(row['label']+'.stderr')
        assert sha(stdout)==row['stdout_sha256'] and sha(stderr)==row['stderr_sha256']
        try:decoded=json.loads(stdout.read_bytes())
        except (ValueError,UnicodeDecodeError):decoded=None
        assert decoded==row['upstream_result']
        if row['timeout']:status='NOT_SOLVED_EXTERNAL_TIMEOUT';assert row['seconds']>=60
        elif row['exit_code']:status='EXECUTION_ERROR_NOT_EVALUATED'
        elif not isinstance(decoded,dict):status='NO_VALID_UPSTREAM_RESULT'
        elif decoded.get('failure'):status='UPSTREAM_REPORTED_FAILURE'
        elif decoded.get('unrealizable')is True:status='UPSTREAM_REPORTED_UNREALIZABLE'
        elif isinstance(decoded.get('solution'),str):status='UPSTREAM_REPORTED_REALIZABLE'
        else:status='UNCLASSIFIED_UPSTREAM_JSON'
        assert status==row['status'];counts[status]+=1
        if status!='UPSTREAM_REPORTED_REALIZABLE':continue
        try:
            projection=project(path.read_text(encoding='utf-8'))
            result=certify_solution(projection['public'],decoded['solution'])
        except ValueError as error:
            excluded.append({'label':row['label'],'path':row['path'],'status':'UNSUPPORTED_ADAPTER_NO_CLAIM','reason':str(error)});continue
        save(output/(row['label']+'.certificate.json'),{'projection':projection,'result':result})
        if not result['accepted']:
            excluded.append({'label':row['label'],'path':row['path'],'status':result['status']});continue
        public,proposal,kernel=projection['public'],result['proposal'],result['kernel']
        own=independent_obligations(public,proposal);h=z3.Int('head')
        left=eval_z3(kernel['singleton'],[h]);right=eval_z3(kernel['step'],[h]+[z3.IntVal(e) for e in kernel['empty']])
        own['EMITTED_SINGLETON_BINDING']=z3.And(*[l==r for l,r in zip(left,right)])
        for name,theorem in own.items():
            solver=z3.Solver();solver.set(timeout=2000);solver.add(z3.Not(theorem));assert solver.check()==z3.unsat,(row['label'],name);proofs+=1
        for query in result['attempts'][-1]['certificate']['obligations']+[result['singleton_binding']]:
            solver=z3.Solver();solver.set(timeout=2000);solver.from_string(query['smt2']);assert solver.check()==z3.unsat;serialized+=1
        for xs in sequences:
            ref=independent_fold(public,xs)
            if row['path'] in ['list/sum.ml','list/mps.ml','list/mts.ml','list/mss.ml']:
                assert ref==mathematical_reference(Path(row['path']).stem,xs)
            for shape in ['LEFT','RIGHT','BALANCED']:
                state=independently_execute(kernel,shaped(xs,shape));assert eval_z3_if_numeric(proposal['decode'],state)==ref;numeric+=1
        certified.append({'label':row['label'],'path':row['path'],'latent_width':len(kernel['empty'])})
    assert dict(counts)==r['status_counts'] and r['whole_seconds']>=sum(x['seconds'] for x in rows)
    installation=read(first/'extracted/build-evidence/cvc4-install.json')
    assert sha(first/'extracted/build-evidence/cvc4-install.log')==installation['log_sha256']
    result={'status':'PASS_CVC4_FIRST_HASH_AND_ADAPTED_KERNEL_AUDIT','archive_files_checked':archive_files,
            'manifest_files_checked':len(manifest),'original_workers':len(rows),'original_status_counts':dict(counts),
            'original_whole_seconds':r['whole_seconds'],'cvc4_install_seconds':installation['seconds'],
            'certified_adapted_emitted_kernels':certified,'unsupported_or_uncertified':excluded,
            'independent_Z3_AST_conditions':proofs,'serialized_CVC5_queries_replayed_Z3':serialized,
            'independent_numeric_constructor_checks':numeric,'first_report_sha256':sha(p/'report.json'),
            'first_manifest_sha256':sha(p/'manifest.json'),'same_original_binary_and_cpu':True,
            'original_CVC5_first_preserved':True,'original_protocol_independently_certified':False,
            'scope':'adapted mathematical fold only; original OCaml repr/target/attributes/overflow not replayed',
            'performance_headroom_claim':False,'learning_performed':False,'fresh_eligible':0,'G1_admitted':False}
    save(output/'report.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['certified_adapted_emitted_kernels','unsupported_or_uncertified']},indent=2))


def eval_z3_if_numeric(program,state):
    from experiments.recursive_summary_replay import eval_program
    return eval_program(program,state)


if __name__=='__main__':audit(*(Path(x) for x in sys.argv[1:]))
