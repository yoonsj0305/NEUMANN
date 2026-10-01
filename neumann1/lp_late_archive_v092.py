"""Byte-exact loading of the first late-pruning audit."""
import gzip,hashlib,io,json
from pathlib import Path


def load_screen(path):
    path=Path(path);m=json.loads(path.read_text())
    if (m['format']!='neumann.lp-late-pruning-screen.archive.v1' or
        m['preregistration_head']!='154ca566e70f3c87e2bdb0a4267e8185e46c9414' or m['rerun'] is not False):
        raise ValueError('screen manifest drift')
    blocks=[];seen=set()
    for part in m['parts']:
        name=part['name']
        if type(name) is not str or Path(name).name!=name or name in seen:
            raise ValueError('unsafe or duplicate archive part')
        seen.add(name);data=(path.parent/name).read_bytes()
        if len(data)!=part['bytes'] or hashlib.sha256(data).hexdigest()!=part['sha256']:
            raise ValueError('archive part integrity drift')
        blocks.append(data)
    data=b''.join(blocks)
    if len(data)!=m['gzip_bytes'] or hashlib.sha256(data).hexdigest()!=m['gzip_sha256']:
        raise ValueError('combined screen integrity drift')
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:raw=stream.read(128*1024*1024+1)
    if len(raw)>128*1024*1024 or len(raw)!=m['json_bytes'] or hashlib.sha256(raw).hexdigest()!=m['json_sha256']:
        raise ValueError('decoded screen integrity drift')
    report=json.loads(raw)
    if any(report['summary'][k]!=m[k] for k in ('decision','global_q3','global_q4')):
        raise ValueError('manifest verdict drift')
    return report
