"""Register every callable stress row for native replay; preserve all exclusions."""
from pathlib import Path
import hashlib,json,zipfile


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def run(work):
    repo=work/'GitHub/NEUMANN';stress=work/'Continuation/FUNCTIONAL_STRESS_FIRST';report=json.loads((stress/'report.json').read_text())
    for n,h in json.loads((stress/'manifest.json').read_text()).items():assert sha(stress/n)==h
    prep=work/'Continuation/SUFU_WITNESS_PREPARATION';prep.mkdir();cases=[];exclusions=[]
    native=work/'Continuation/SUFU_NATIVE_FIRST/neumann-sufu/native-suite-first'
    for c in report['cases_detail']:
        rows=[(i,r)for i,r in enumerate(c['rows'])if r['status']in{'CONCRETE_MATCH','CONCRETE_COUNTEREXAMPLE'}]
        exclusions.append({'index':c['index'],'original_path':c['original_path'],'stress_status':c['status'],'included_rows':len(rows),'excluded_rows':len(c['rows'])-len(rows)})
        if not rows:continue
        f=prep/f"{c['index']:03}.inputs.json";g=prep/f"{c['index']:03}.expected.json"
        save(f,[{'entrypoint':r['original_named_entrypoint'],'inputs':r['inputs'],'arguments':r['arguments']}for _,r in rows])
        save(g,[{'row_id':i,'python_status':r['status'],'original':r['original_output'],'optimized':r['transformed_output']}for i,r in rows])
        cases.append({'index':c['index'],'original_path':c['original_path'],'original_sha256':c['original_sha256'],'optimized_sha256':c['optimized_sha256'],
                      'inputs_file':f.name,'inputs_sha256':sha(f),'expected_file':g.name,'expected_sha256':sha(g),'rows':len(rows)})
    runner=repo/'experiments/sufu_native_witness.py';adapter=repo/'experiments/sufu_source_witness.cpp'
    reg={'study':'SUFU_OPENED_NATIVE_WITNESS_REPLAY_V1','cases':cases,'all_290_exposure_and_exclusions':exclusions,
         'selection':'All stress rows with successful guarded original AND optimized concrete executions, irrespective of matching; no resampling',
         'stress_report_sha256':sha(stress/'report.json'),'native_first_report_sha256':sha(native/'report.json'),
         'runner_sha256':sha(runner),'adapter_source_sha256':sha(adapter),'adapter_source':'/kaggle/working/neumann-resume/sufu_source_witness.cpp',
         'binary':'/kaggle/working/neumann-resume/sufu-witness-build-first/source-witness','binary_sha256':'76931c4d3f5f8ff8404e1196e96e97373379a5951a776d47a1948606febbed1b',
         'per_program_seconds':10,'execution':'Sequential upstream parse/evaluate; no concurrent rand-named frontend files',
         'semantics':'Pinned author C++ evaluator; guarded signed32 first-order witnesses; not universal proof or general overflow safety',
         'fresh_eligible':0,'official_score':False,'G0_passed':False,'G1_admitted':False,'G2_admitted':False}
    save(prep/'registration.json',reg);save(prep/'freeze.json',{'registration_sha256':sha(prep/'registration.json')})
    (prep/'runner.py').write_bytes(runner.read_bytes());(prep/'source-witness.cpp').write_bytes(adapter.read_bytes())
    archive=prep/'SUFU_WITNESS_INPUTS.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED)as z:
        for p in prep.iterdir():
            if p.is_file()and p!=archive:z.write(p,p.name)
    print('FROZEN',sha(prep/'registration.json'),'cases',len(cases),'rows',sum(c['rows']for c in cases),'archive_bytes',archive.stat().st_size,'archive_sha256',sha(archive))


if __name__=='__main__':run(Path(__file__).resolve().parents[3])
