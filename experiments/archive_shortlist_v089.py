"""Preserve the completed gzip byte-exact, never rerun fitting or evaluation."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('completed_gzip',type=Path)
    args=parser.parse_args()
    data=args.completed_gzip.read_bytes(); decoded=gzip.decompress(data); report=json.loads(decoded)
    if report['stage']!='completed': raise ValueError('completed first audit required')
    root=Path('docs/experiments/results'); parts=[]
    for i,start in enumerate(range(0,len(data),8388608)):
        content=data[start:start+8388608]; name=f'v089_completed.json.gz.part{chr(97+i//26)}{chr(97+i%26)}'
        with (root/name).open('xb') as stream: stream.write(content)
        parts.append({'name':name,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
    manifest={'format':'neumann.lp-shortlist-study.archive.v1',
        'preregistration_head':'b2e73ef6410adb07bebef484e2ba5299163cdaa1','rerun':False,
        'parts':parts,'gzip_bytes':len(data),'gzip_sha256':hashlib.sha256(data).hexdigest(),
        'json_bytes':len(decoded),'json_sha256':hashlib.sha256(decoded).hexdigest(),
        **{k:report['summary'][k] for k in ('decision','global_q3','global_q4')}}
    with (root/'v089_completed.manifest.json').open('x') as stream:
        json.dump(manifest,stream,indent=2); stream.write('\n')
    # Screen bytes are preserved separately, not inserted into the timed study.
    screen=(root/'v089_training_shortlist_screen.json').read_bytes()
    with (root/'v089_training_shortlist_screen.json.gz').open('xb') as stream:
        stream.write(gzip.compress(screen,mtime=0))
    print(json.dumps(manifest,indent=2))


if __name__=='__main__': main()
