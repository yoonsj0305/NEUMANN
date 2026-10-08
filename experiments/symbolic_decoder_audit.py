"""Independent replay and union of existing native evidence, without resynthesis."""
from pathlib import Path
import hashlib,itertools,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.recursive_summary_replay import independent_obligations,eval_program
from experiments.synduce_full_baseline_audit import independent_fold,shaped


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def save(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def fold(proposal,tree):
    if tree[0]=='nil':return list(proposal['empty'])
    if tree[0]=='single':return eval_program(proposal['step'],[tree[1]]+proposal['empty'])
    return eval_program(proposal['merge'],fold(proposal,tree[1])+fold(proposal,tree[2]))


def audit(opened,preparation,first,output):
    import z3
    assert not output.exists();output.mkdir(parents=True)
    assert sha(preparation/'preregister.json')=='bfc73191dfe74d89feebc809032e94e7ae0e70d7dac8fa0a15102414c8e97e61'
    assert sha(first/'report.json')=='19996ad5fdd0f9510a9d3851efa39dfae8cd4112ba65eb5801367cb82e38b05b'
    assert sha(first/'manifest.json')=='45aa6a7129b92592ec3cfda3e9e6b4c25b1aacba634603557e69b73e9e8e247e'
    contract=read(preparation/'preregister.json')
    assert sha(opened/'manifest.json')==contract['opened_manifest_sha256']
    old_manifest=read(opened/'manifest.json');manifest=read(first/'manifest.json')
    for base,items in [(opened,old_manifest),(first,manifest)]:
        for name,pin in items.items():
            path=(base/name).resolve();assert path.is_relative_to(base.resolve()) and sha(path)==pin
    for name,pin in contract['sources'].items():assert sha(ROOT/name)==sha(preparation/'source'/name)==pin
    selected=[];proofs=saved=rows=0;registry=read(opened/'registry.json')
    for key,asset in sorted(registry['public'].items()):
        public=read(first/'public'/(key+'.json'));found=read(first/'native'/(key+'.json'))
        if found['accepted']:
            proposal=found['proposal'];cert=found['certificate'];route='NEW_SYMBOLIC_DECODER_FIRST'
        else:
            # Retained native finite-response evidence supplies the two separate
            # successes. This does not change the new generator's 25/27 result.
            previous=read(opened/'native'/'GENERATED_FINITE_RESPONSE'/(key+'.json'))
            assert previous['accepted'];proposal=previous['native']['proposal'];cert=previous['certificate'];route='PRIOR_FINITE_RESPONSE_FIRST'
        for name,theorem in independent_obligations(public,proposal).items():
            solver=z3.Solver();solver.set(timeout=2000);solver.add(z3.Not(theorem));assert solver.check()==z3.unsat,(key,name);proofs+=1
        for lemma in cert['obligations']:
            solver=z3.Solver();solver.set(timeout=2000);solver.from_string(lemma['smt2']);assert solver.check()==z3.unsat;saved+=1
        for n in range(7):
            for values in itertools.product([-2,0,3],repeat=n):
                expected=independent_fold(public,list(values))
                for shape in ['LEFT','RIGHT','BALANCED']:
                    assert eval_program(proposal['decode'],fold(proposal,shaped(values,shape)))==expected;rows+=1
        selected.append({'public_AST_sha256':key,'route':route,'proposal':proposal,'certificate':cert,
          'opened_source_asset':asset,'role':'O_OFFLINE_ONLY','training_allowed':False,'fresh_eligible':False})
    termination=0
    for item in read(first/'source-inventory.json'):
        if item['status']=='UNSUPPORTED_SOURCE_PROTOCOL_NO_CLAIM':continue
        binding=read(first/'bindings'/(item['label']+'.json'))
        assert binding['source_sha256']==item['source']['sha256']
        assert all(x['word_actual']==x['word_expected'] for x in binding['flatten_proof']['clause_records'])
        for lemma in binding['flatten_proof']['proof_records']:
            solver=z3.Solver();solver.set(timeout=2000);solver.from_string(lemma['termination_smt2']);assert solver.check()==z3.unsat;termination+=1
    save(output/'native-union.json',selected)
    result={'status':'PASS_INDEPENDENT_NATIVE_UNION_AUDIT','new_generator_first_certified':25,
      'new_generator_first_abstained':2,'prior_native_finite_successes_reused':2,'native_union_opened_ASTs':len(selected),
      'independent_Z3_conditions':proofs,'saved_CVC5_conditions_in_Z3':saved,
      'independent_numeric_rows_length0_to6':rows,'source_termination_conditions_in_Z3':termination,
      'first_manifest_files_checked':len(manifest),'prior_manifest_files_checked':len(old_manifest),
      'first_report_sha256':sha(first/'report.json'),'first_manifest_sha256':sha(first/'manifest.json'),
      'union_is_new_performance_experiment':False,'global_optimality':False,'G0_passed':False,'G1_admitted':False,
      'learning_performed':False,'fresh_eligible':0}
    save(output/'audit.json',result);save(output/'manifest.json',{str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file()})
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':audit(*(Path(p) for p in sys.argv[1:]))
