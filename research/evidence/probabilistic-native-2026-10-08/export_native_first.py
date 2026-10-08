"""Archive completed first receipts without rerunning any solver."""
from pathlib import Path
from IPython.display import HTML, display
import base64
import hashlib
import json
import zipfile

root = Path('/kaggle/working/neumann_probabilistic')
assert (root/'native-first/report-first.json').is_file(), 'Do not snapshot a running first experiment'
files = sorted(p for p in root.rglob('*') if p.is_file() and
               'deps' not in p.relative_to(root).parts and
               '__pycache__' not in p.relative_to(root).parts and
               p.name != 'export-manifest-first.json')
manifest = {'kind': 'FIRST_NATIVE_CPU_EVIDENCE_EXPORT',
            'files': [{'name': p.relative_to(root).as_posix(),
                       'bytes': p.stat().st_size,
                       'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files],
            'excluded': ['installed wheel dependencies; package identities remain in install-first.json', 'Python bytecode'],
            'rerun': False}
with (root/'export-manifest-first.json').open('x') as stream:
    json.dump(manifest, stream, indent=2)
archive = Path('/kaggle/working/PROBABILISTIC_NATIVE_FIRST.zip')
with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as bundle:
    for p in files + [root/'export-manifest-first.json']:
        bundle.write(p, p.relative_to(root).as_posix())
data = archive.read_bytes()
print(json.dumps({'file': archive.name, 'bytes': len(data), 'entries': len(files)+1,
                  'sha256': hashlib.sha256(data).hexdigest(), 'rerun': False}), flush=True)
display(HTML('<a download="PROBABILISTIC_NATIVE_FIRST.zip" href="data:application/zip;base64,'+
             base64.b64encode(data).decode()+'">Download first probabilistic CPU evidence</a>'))
