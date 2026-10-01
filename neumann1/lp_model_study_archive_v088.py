"""Immutable first-study byte loading; never generate inputs or fit a model."""
import gzip
import hashlib
import io
import json
from pathlib import Path


def load_study(path):
    path=Path(path)
    manifest=json.loads(path.read_text())
    if (manifest['format']!='neumann.lp-first-model-study.archive.v1'
            or manifest['preregistration_head']!='e3d7042d57b872ab61756c3b4103607c2f3e43cf'
            or manifest['rerun'] is not False):
        raise ValueError('first-study manifest drift')
    parts=[]; seen=set()
    for part in manifest['parts']:
        name=part['name']
        if type(name) is not str or Path(name).name!=name or name in seen:
            raise ValueError('unsafe/duplicate archive part')
        seen.add(name)
        data=(path.parent/name).read_bytes()
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
    if (report['summary']['decision']!=manifest['decision']
            or report['summary']['global_q3']!=manifest['global_q3']
            or report['summary']['global_q4']!=manifest['global_q4']):
        raise ValueError('manifest decision drift')
    return report
