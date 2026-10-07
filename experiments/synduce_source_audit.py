"""Integrity and conservative compatibility inventory of opened upstream sources."""
from __future__ import annotations
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

from neumann1.synduce_reference import reference_projection, uncomment


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(intake: Path, output: Path) -> dict:
    output.mkdir(exist_ok=False, parents=True)
    manifest = json.loads((intake / 'manifest.json').read_text())
    assert digest((intake / 'upstream.zip').read_bytes()) == manifest['archive_sha256']
    prefix = 'Synduce-' + manifest['commit'] + '/'
    checked = 0
    inventory = []
    groups = defaultdict(list)
    with zipfile.ZipFile(intake / 'upstream.zip') as archive:
        for row in manifest['files']:
            original = archive.read(prefix + row['path'])
            local = (intake / 'upstream' / row['local_path']).read_bytes()
            assert local == original
            assert len(local) == row['bytes'] and digest(local) == row['sha256']
            checked += 1
            if not row['path'].startswith('benchmarks/') or not row['path'].endswith(('.ml','.pmrs')):
                continue
            source = local.decode('utf-8')
            clean = uncomment(source)
            item = {'path': row['path'], 'sha256': row['sha256'],
                    'public_source': True, 'role': 'OPENED_DEVELOPMENT', 'fresh_eligible': False,
                    'directory': str(Path(row['path']).parent).replace('\\','/'),
                    'extension': Path(row['path']).suffix,
                    'source_requires': '[@@requires' in clean,
                    'source_ensures': '[@@ensures' in clean,
                    'unknown_markers': len(re.findall(r'\[%synt\b', clean)),
                    'upstream_declared_options': re.findall(r'@synduce([^*]*)', source)}
            try:
                projected = reference_projection(source)
                payload = json.dumps(projected, sort_keys=True, separators=(',',':')).encode()
                key = digest(payload)
                (output / 'public').mkdir(exist_ok=True)
                path = output / 'public' / (key + '.json')
                if path.exists():
                    assert path.read_bytes() == payload
                else:
                    path.write_bytes(payload)
                item.update({'reference_projection': 'SUPPORTED_RESTRICTED_MATH_INTEGER_FOLD',
                             'projection_sha256': key, 'original_output_width': len(projected['empty']),
                             'official_target_or_repr_checked': False})
                groups[key].append(row['path'])
            except ValueError as error:
                item.update({'reference_projection': 'UNSUPPORTED_NO_CLAIM',
                             'reason': str(error), 'official_target_or_repr_checked': False})
            inventory.append(item)
    counts = Counter(item['reference_projection'] for item in inventory)
    report = {'kind': 'OPENED_SOURCE_INTEGRITY_AND_COMPATIBILITY_ONLY',
              'commit': manifest['commit'], 'checked_files': checked,
              'benchmark_source_files': len(inventory), 'projection_counts': dict(counts),
              'distinct_exact_public_fold_ASTs': len(groups),
              'AST_equality_is_independence_proof': False,
              'duplicate_projection_groups': dict(groups),
              'sources_with_requires': sum(item['source_requires'] for item in inventory),
              'fresh_eligible': 0, 'training_admitted': False,
              'benchmarks_executed': False,
              'scope': 'Whole ZIP integrity; first Nil/Cons projection only, not whole program or upstream benchmark replay'}
    (output / 'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    (output / 'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return {k:v for k,v in report.items() if k != 'duplicate_projection_groups'}


if __name__ == '__main__':
    print(json.dumps(audit(Path(sys.argv[1]),Path(sys.argv[2]))))
