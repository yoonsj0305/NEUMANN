"""Retrieve original native-format sources from the same pinned public lineage."""
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib
import json
import sys
sys.set_int_max_str_digits(100_000)
root = Path(__file__).resolve().parent
manifest = json.loads((root / 'source-cases-first.json').read_text())
rows = []
for case in manifest['cases']:
    meta = json.loads((root / 'public-source-metadata' / (case['family'] + '.json')).read_text())
    file = next(x for x in meta['files'] if x['file'] == case['file'])
    originals = []
    for name in file.get('original-file', []):
        url = f"https://raw.githubusercontent.com/ahartmanns/qcomp/{case['source_commit']}/benchmarks/dtmc/{case['family']}/{name}"
        target = root / 'native-inputs' / case['family'] / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with urlopen(Request(url, headers={'User-Agent': 'NEUMANN-public-source-audit'}), timeout=30) as response:
                data = response.read(8_000_001)
            assert len(data) <= 8_000_000
            with target.open('xb') as out:
                out.write(data)
        data = target.read_bytes()
        originals.append({'name': name, 'url': url, 'sha256': hashlib.sha256(data).hexdigest(),
                          'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(),
                          'bytes': len(data)})
    prism = next((x for x in originals if x['name'].endswith(('.pm', '.prism'))), None)
    props = next((x for x in originals if x['name'].endswith(('.props', '.prctl'))), None)
    rows.append({'case_id': case['case_id'], 'family': case['family'], 'originals': originals,
                 'prism': prism, 'properties': props,
                 'comparison_status': 'NATIVE_PRISM_AVAILABLE' if prism and props else 'JANI_ONLY_PGCL_CONVERSION'})
with (root / 'native-sources-first.json').open('x') as out:
    json.dump({'source_commit': manifest['cases'][0]['source_commit'], 'rows': rows}, out, indent=2)
for row in rows:
    print(row['case_id'], row['comparison_status'], [(x['name'], x['bytes']) for x in row['originals']])
