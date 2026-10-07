"""Preserve native first artifacts in bounded browser-transfer chunks."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path('/kaggle/working/neumann-sufu')
EXPORT=Path('/kaggle/working/neumann-resume/sufu-native-export')


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def export():
    report=json.loads((ROOT/'native-suite-first/report.json').read_text())
    assert report['benchmark_count']==290 and report['status']=='COMPLETED_OPENED_ENGINEERING_ONLY'
    assert not EXPORT.exists();EXPORT.mkdir()
    paths=set(p for p in ROOT.glob('*.json')if p.is_file())
    for d in ['native-suite-first','preflight-sum','bootstrap-logs','repair-logs']:
        paths.update(p for p in(ROOT/d).rglob('*')if p.is_file())
    paths.update([ROOT/'build-jsoncpp/executor/run',ROOT/'source/src/surface/f',
                  ROOT/'build-jsoncpp/executor/CMakeFiles/run.dir/flags.make',
                  ROOT/'build-jsoncpp/executor/CMakeFiles/run.dir/link.txt',ROOT/'build-jsoncpp/CMakeCache.txt'])
    launch=Path('/kaggle/working/neumann-resume/sufu-native-registration')
    paths.update(p for p in launch.rglob('*')if p.is_file())
    archive=EXPORT/'SUFU_NATIVE_FIRST.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for p in sorted(paths):
            assert p.is_file(),str(p)
            z.write(p,p.relative_to('/kaggle/working').as_posix())
    raw=archive.read_bytes();parts=[]
    for i,start in enumerate(range(0,len(raw),2*1024*1024)):
        p=EXPORT/f'part-{i:03}.bin';p.write_bytes(raw[start:start+2*1024*1024])
        parts.append({'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p)})
    receipt={'status':'FIRST_RECORDS_AND_EXECUTABLE_PRESERVED','archive':archive.name,'bytes':len(raw),
             'sha256':sha(archive),'members':len(paths),'parts':parts,'complete_dependency_closure':False,
             'native_first_report_sha256':sha(ROOT/'native-suite-first/report.json'),
             'native_first_manifest_sha256':sha(ROOT/'native-suite-first/manifest.json'),
             'binary_sha256':sha(ROOT/'build-jsoncpp/executor/run'),'counts':report['counts'],
             'whole_native_seconds':report['sequential_suite_seconds'],'no_score_or_cost_advantage_claim':True}
    (EXPORT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':export()
