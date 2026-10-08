"""Check immutable opened archive transport; never extract or execute members."""
import argparse
import hashlib
import json
from pathlib import Path


def verify(root):
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    results=[]
    for row in manifest['originals']:
        total=hashlib.sha256()
        size=0
        for part in row['parts_in_order']:
            path=(root/part['file']).resolve()
            if not path.is_relative_to(root.resolve()):
                raise ValueError('Part outside transport root')
            payload=path.read_bytes()
            if len(payload)!=part['bytes'] or hashlib.sha256(payload).hexdigest()!=part['sha256']:
                raise ValueError('Part identity mismatch: '+part['file'])
            total.update(payload)
            size+=len(payload)
        if size!=row['bytes'] or total.hexdigest()!=row['sha256']:
            raise ValueError('Archive identity mismatch: '+row['original_file'])
        results.append(row)
    return results


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--archive')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if bool(args.archive)!=bool(args.output):
        parser.error('--archive and --output must be provided together')
    root=Path(__file__).resolve().parent
    rows=verify(root)
    if args.archive:
        found=[row for row in rows if row['original_file']==args.archive]
        if len(found)!=1:
            raise ValueError('Archive must match a registered name')
        row=found[0]
        with args.output.open('xb') as stream:
            for part in row['parts_in_order']:
                stream.write((root/part['file']).read_bytes())
        if hashlib.sha256(args.output.read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('Written archive identity mismatch')
    print(json.dumps({'status':'PASS','archives':len(rows),
                      'bytes':sum(row['bytes'] for row in rows),
                      'scientific_results_changed':False},indent=2))


if __name__=='__main__':
    main()
