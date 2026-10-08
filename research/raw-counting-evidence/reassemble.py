"""Verify immutable ordered transport parts; optionally write a new archive."""
import argparse
import hashlib
import json
from pathlib import Path


def verify(root):
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    total_hash = hashlib.sha256()
    total_bytes = 0
    parts = []
    for row in manifest['parts_in_order']:
        name = row['file']
        if Path(name).name != name:
            raise ValueError('Part name must be a direct child')
        payload = (root / name).read_bytes()
        if len(payload) != row['bytes'] or hashlib.sha256(payload).hexdigest() != row['sha256']:
            raise ValueError('Part identity mismatch: ' + name)
        total_hash.update(payload)
        total_bytes += len(payload)
        parts.append(root / name)
    if total_bytes != manifest['original_bytes'] or total_hash.hexdigest() != manifest['original_sha256']:
        raise ValueError('Joined archive identity mismatch')
    return manifest, parts


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    manifest, parts = verify(Path(__file__).resolve().parent)
    if args.output:
        with args.output.open('xb') as output:
            for part in parts:
                output.write(part.read_bytes())
        if hashlib.sha256(args.output.read_bytes()).hexdigest() != manifest['original_sha256']:
            raise ValueError('Written archive identity mismatch')
    print(json.dumps({'status': 'PASS', 'bytes': manifest['original_bytes'],
                      'sha256': manifest['original_sha256'], 'parts': len(parts),
                      'first_verdict': manifest['first_verdict']}, indent=2))


if __name__ == '__main__':
    main()
