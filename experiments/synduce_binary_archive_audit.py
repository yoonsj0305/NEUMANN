"""Inbound compiled artifact audit; no re-execution or new score."""
import hashlib,json,sys,zipfile
from pathlib import Path


def digest(data):return hashlib.sha256(data).hexdigest()


def audit(first, output):
    archive=first/'NEUMANN_FULL_SYNDUCE_FIRST.zip'
    assert digest(archive.read_bytes())=='9d1953ab3446419b45e1dc8edda04ee3c189b62cf10cbbe2b34b03fdf1ca1bf5'
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))==205
        compiled=z.read('compiled/main.exe')
        binary_pin=json.loads((first/'extracted/baseline-first/runtime.json').read_text())['binary_sha256']
        assert digest(compiled)==binary_pin
        assert compiled[:4]==b'\x7fELF', 'Kaggle Linux executable,not runnable on Windows'
        checked=0
        for name in z.namelist():
            if name=='compiled/main.exe':continue
            assert (first/'extracted'/name).read_bytes()==z.read(name),name
            checked+=1
        export=z.read('build-evidence/switch.export')
        manifest={name:digest(z.read(name)) for name in z.namelist()}
    assert not output.exists();output.mkdir(parents=True)
    (output/'archive-members.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    result={'status':'PASS_INBOUND_COMPILED_ARTIFACT_AUDIT','archive_sha256':digest(archive.read_bytes()),
            'archive_bytes':archive.stat().st_size,'archive_members':len(manifest),'previous_record_files_byte_equal':checked,
            'binary_sha256':binary_pin,'binary_bytes':len(compiled),'opam_export_sha256':digest(export),
            'binary_format':'Linux ELF','Windows_local_execution_performed':False,
            'complete_dependency_environment_preserved':False,'first_performance_result_changed':False}
    (output/'audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':audit(*(Path(p) for p in sys.argv[1:]))
