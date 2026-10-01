"""Byte-verified loading of the first frozen-checkpoint shortlist audit."""
import gzip
import hashlib
import io
import json
from pathlib import Path


def load_study(path):
    path=Path(path); manifest=json.loads(path.read_text())
    if (manifest['format']!='neumann.lp-shortlist-study.archive.v1'
            or manifest['preregistration_head']!='b2e73ef6410adb07bebef484e2ba5299163cdaa1'
            or manifest['rerun'] is not False):
        raise ValueError('shortlist manifest drift')
    parts=[]; seen=set()
    for part in manifest['parts']:
        name=part['name']
        if type(name) is not str or Path(name).name!=name or name in seen:
            raise ValueError('unsafe/duplicate archive part')
        seen.add(name); data=(path.parent/name).read_bytes()
        if len(data)!=part['bytes'] or hashlib.sha256(data).hexdigest()!=part['sha256']:
            raise ValueError('archive part integrity drift')
        parts.append(data)
    data=b''.join(parts)
    if len(data)!=manifest['gzip_bytes'] or hashlib.sha256(data).hexdigest()!=manifest['gzip_sha256']:
        raise ValueError('combined archive integrity drift')
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream: decoded=stream.read(128*1024*1024+1)
    if (len(decoded)>128*1024*1024 or len(decoded)!=manifest['json_bytes']
            or hashlib.sha256(decoded).hexdigest()!=manifest['json_sha256']):
        raise ValueError('decoded archive integrity drift')
    report=json.loads(decoded)
    if any(report['summary'][k]!=manifest[k] for k in ('decision','global_q3','global_q4')):
        raise ValueError('manifest decision drift')
    return report
